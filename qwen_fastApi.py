import asyncio
import json
import os
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from modelscope import AutoTokenizer
from modelscope import GenerationConfig, snapshot_download
from sse_starlette.sse import EventSourceResponse
from vllm import AsyncEngineArgs, AsyncLLMEngine
from vllm import SamplingParams
from vllm import TokensPrompt

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model_dir = "qwen/Qwen2.5-0.5B-Instruct"
#model_dir = "Qwen/Qwen2.5-7B-Instruct"

tensor_parallel_size = 2
gpu_memory_utilization = 0.6
dtype = "float16"
temperature: float = 0.7
top_p = 0.8
repetition_penalty = 1.05
max_tokens = 512

system_prompt = '''
你擅长通过视频字幕总结视频的核心主题和内容，具体要求如下：
请提供该视频的核心主题和主要内容。
根据字幕，概括视频中涉及的主要论点或事件。
请包括视频的关键信息、讲述的故事或讨论的重点。
如果有多个部分，请简要总结每一部分的内容，并突出最重要的细节。
如果有结论或主要的建议，请在总结中注明。
'''


def format_sse(data: str, finished: bool = False) -> str:
    """格式化SSE消息"""
    return json.dumps({
                'content': data,
                'finished': finished
            }, ensure_ascii=False)


async def generate_llm_response(prompt: str) -> AsyncGenerator[str, None]:
    # vLLM请求配置
    sampling_params = SamplingParams(top_p=top_p,
                                     temperature=temperature,
                                     repetition_penalty=repetition_penalty,
                                     max_tokens=max_tokens)
    # vLLM异步推理（在独立线程中阻塞执行推理，主线程异步等待完成通知）
    request_id = str(uuid.uuid4().hex)
    results_iter = engine.generate(prompt=prompt, sampling_params=sampling_params, request_id=request_id)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    input_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    print(input_text)
    results_iter = engine.generate(prompt=input_text, sampling_params=sampling_params, request_id=request_id)

    async for result in results_iter:
        # 移除im_end,eos等系统停止词
        # 返回截止目前的tokens输出
        text = tokenizer.decode(result.outputs[0].token_ids)
        yield format_sse(text, False)

    # 发送结束标记
    yield format_sse(text, True)


def load_stream_vllm():
    global generation_config, tokenizer, stop_words_ids, engine
    # 模型下载
    snapshot_download(model_dir)
    # 模型基础配置
    generation_config = GenerationConfig.from_pretrained(model_dir, trust_remote_code=True)
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
    tokenizer.eos_token_id = generation_config.eos_token_id
    # 推理终止词
    stop_words_ids = [tokenizer.eos_token_id]
    # vLLM基础配置
    args = AsyncEngineArgs(model_dir)
    args.worker_use_ray = False
    args.engine_use_ray = False
    args.tokenizer = model_dir
    args.tensor_parallel_size = tensor_parallel_size
    args.trust_remote_code = True
    # args.quantization=quantization
    args.gpu_memory_utilization = gpu_memory_utilization
    args.dtype = dtype
    args.max_num_seqs = 20  # batch最大20条样本
    # 加载模型
    os.environ['VLLM_USE_MODELSCOPE'] = 'True'
    engine = AsyncLLMEngine.from_engine_args(args)
    return generation_config, tokenizer, stop_words_ids, engine


generation_config, tokenizer, stop_words_ids, engine = load_stream_vllm()


@app.post("/chat")
async def chat(request: Request):
    """
    基本的SSE实现
    """
    data = await request.json()
    prompt = data.get("prompt", "")

    async def event_generator():
        async for response in generate_llm_response(prompt):
            if await request.is_disconnected():
                break
            yield {
                "data": response
            }

    return EventSourceResponse(event_generator())


# 如果需要更细粒度的控制，可以使用StreamingResponse
@app.post("/chatV2")
async def stream_summary_raw(request: Request):
    """
    使用StreamingResponse的实现
    """
    data = await request.json()
    prompt = data.get("prompt", "")

    async def generate():
        async for response in generate_llm_response(prompt):
            yield f"data: {response}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# 发布订阅模式的实现
SUBSCRIBERS = set()


async def subscribe(request: Request):
    queue = asyncio.Queue()
    SUBSCRIBERS.add(queue)
    try:
        while True:
            if await request.is_disconnected():
                break
            data = await queue.get()
            yield data
    finally:
        SUBSCRIBERS.remove(queue)


@app.get("/api/v1/subscribe")
async def subscribe_endpoint(request: Request):
    return EventSourceResponse(subscribe(request))


@app.post("/api/v1/publish")
async def publish(request: Request):
    data = await request.json()
    message = data.get("message")

    if not message:
        return {"error": "No message provided"}

    for queue in SUBSCRIBERS:
        await queue.put({
            "data": json.dumps({"message": message})
        })

    return {"status": "published"}


# 心跳机制的实现
async def heartbeat():
    """
    发送心跳保持连接活跃
    """
    while True:
        for queue in SUBSCRIBERS:
            await queue.put({
                "event": "ping",
                "data": "keepalive"
            })
        await asyncio.sleep(15)  # 每15秒发送一次心跳


@app.on_event("startup")
async def startup_event():
    """
    应用启动时启动心跳任务
    """
    asyncio.create_task(heartbeat())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=None, port=8000, log_level="debug")

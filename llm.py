from modelscope import AutoModelForCausalLM, AutoTokenizer
from flask import Flask, request

app = Flask(__name__)

model_name = "Qwen/Qwen2.5-7B-Instruct"
system_prompt = '''
你擅长通过视频字幕总结视频的核心主题和内容，具体要求如下：
请提供该视频的核心主题和主要内容。
根据字幕，概括视频中涉及的主要论点或事件。
请包括视频的关键信息、讲述的故事或讨论的重点。
如果有多个部分，请简要总结每一部分的内容，并突出最重要的细节。
如果有结论或主要的建议，请在总结中注明。
'''


def call_llm(prompt):
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512,
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print("response: " + response)
    return response


@app.route('/summary', methods=['POST'])
def get_summary():
    prompt = request.json['prompt']
    print("start summary, prompt: " + prompt)
    return {
        "summary": call_llm(prompt)
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7002, debug=True)

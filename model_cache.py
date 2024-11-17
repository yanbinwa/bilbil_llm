from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# Pass the default decoding hyperparameters of Qwen2.5-7B-Instruct
# max_tokens is for the maximum length for generation.
sampling_params = SamplingParams(temperature=0.7, top_p=0.8, repetition_penalty=1.05, max_tokens=512)

# Input the model name or path. Can be GPTQ or AWQ models.
llm = LLM(model="Qwen/Qwen2.5-7B-Instruct")

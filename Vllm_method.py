import sys
from datetime import datetime

from vllm import LLM, SamplingParams

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)
# llm = LLM(model="facebook/opt-125m")
llm = LLM(model="Qwen/Qwen2.5-1.5B-Instruct")


def log_exception(func_name, logfile):
    exc_type, exc_obj, tb = sys.exc_info()
    lineno = tb.tb_lineno
    error_message = f"\nIn {func_name} LINE.NO-{lineno} : {exc_obj}"
    print("error_message : ", error_message)
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(error_message)


def process_logger(process, logfile):
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(f'\n{datetime.now()} {process}')


def vllm_query(context, prompt, logfile):
    try:
        input_prompt = f"Context : {context} \n\n instructions : {prompt}\n Answer:"
        outputs = llm.generate(input_prompt, sampling_params)
        results = []
        for output in outputs:
            prompt = output.prompt
            generated_text = output.outputs[0].text
            results.append({
                'prompt': prompt,
                'generated_text': generated_text
            })
        return results
    except:
        log_exception("vllm_query:", logfile)

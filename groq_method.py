from groq import Groq
import json
from datetime import datetime
import sys

client = Groq()
config_data = json.loads(open("config.json", "r+").read())


def log_exception(func_name, logfile):
    exc_type, exc_obj, tb = sys.exc_info()
    lineno = tb.tb_lineno
    error_message = f"\nIn {func_name} LINE.NO-{lineno} : {exc_obj}"
    print("error_message : ", error_message)
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(error_message)


def processLogger(process, logfile):
    with open(logfile, 'a', encoding='utf-8') as fp:
        fp.writelines(f'\n{datetime.now()} {process}')


def groq_method(context, prompt, logfile):
    try:
        input_prompt = f"Context : {context} \n\n instructions : {prompt}\n Answer:"

        completion = client.chat.completions.create(
            model=config_data["groq_model"],
            messages=[
                {
                    "role": "user",
                    "content": input_prompt
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None
        )
        all_res = []
        for chunk in completion:
            res = chunk.choices[0].delta.content or ""
            if res:
                all_res.append(res)
        return all_res
    except:
        log_exception("groq_method:", logfile)
        return []

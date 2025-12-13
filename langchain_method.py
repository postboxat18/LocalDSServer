# pip install -qU langchain "langchain[anthropic]"
from langchain.agents import create_agent

import json
from datetime import datetime
import sys

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


def langchain_method(context, prompt, logfile):
    try:
        agent = create_agent(
            model="claude-sonnet-4-5-20250929",
            tools=[context],
            system_prompt="You are a helpful assistant",
        )

        # Run the agent
        res=agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )
        return res
    except:
        log_exception("langchain_method:", logfile)
        return  ""

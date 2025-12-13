from transformers import AutoTokenizer, AutoModelForCausalLM
import json

config_data = json.loads(open("config.json", "r+").read())
model_name = config_data["ollama_model"]
tokenizer = AutoTokenizer.from_pretrained(model_name, token=config_data["hf_write"])
model = AutoModelForCausalLM.from_pretrained(model_name, token=config_data["hf_write"])


def ollama_method(texts, prompt):
    try:
        input_prompt = f"Context : {texts} \n\n instructions : {prompt}\n Answer:"
        messages = [
            {"role": "user", "content": input_prompt},
        ]

        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)

        outputs = model.generate(**inputs, max_new_tokens=8192)
        res = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])
        return res
    except Exception as e:
        tb = e.__traceback__
        return {"dynamic_query error": f"{str(tb.tb_lineno)},{str(e)}"}

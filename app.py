import json
import os
import sys
from datetime import datetime

import fitz
from flask import Flask, request, send_file

from PDF_editable import add_text_to_pdf, wait_for_pdf_ready
from RAG_method import rag_method
# from Vllm_method import vllm_query
from ocr_process import ocr_method
from groq_method import groq_method
from ollama_method import ollama_method
from langchain_method import langchain_method

outputPath = os.getcwd()
logfile = os.path.join(outputPath, "vllm_flask_log.txt")
app = Flask(__name__)


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


@app.post('/ollama')
def ollama_process():
    try:
        if request.method == 'POST':
            data = request.json
            prompt = data["prompt"]
            inputText = data["text"]
            result = ollama_method(inputText, prompt)
            return json.dumps(result)
        else:
            return {"failed": "400"}

    except Exception as e:
        tb = e.__traceback__
        return {"error": f"{str(tb.tb_lineno)},{str(e)}"}


@app.post('/groq')
def groq_process():
    try:
        if request.method == 'POST':
            data = request.json
            prompt = data["prompt"]
            inputText = data["text"]
            result = groq_method(inputText, prompt,logfile)
            return json.dumps(result)
        else:
            return {"failed": "400"}

    except Exception as e:
        tb = e.__traceback__
        return {"error": f"{str(tb.tb_lineno)},{str(e)}"}



@app.post('/langchain')
def langchain_process():
    try:
        if request.method == 'POST':
            data = request.json
            prompt = data["prompt"]
            inputText = data["text"]
            result = langchain_method(inputText, prompt,logfile)
            return json.dumps(result)
        else:
            return {"failed": "400"}

    except Exception as e:
        tb = e.__traceback__
        return {"error": f"{str(tb.tb_lineno)},{str(e)}"}


# @app.route('/vllm', methods=['POST'])
# def vllm_process():
#     data = request.json
#     prompt = data["prompt"]
#     inputText = data["text"]
#     result = vllm_query(inputText, prompt, logfile)
#     return json.dumps(result)


@app.route('/rag', methods=['POST'])
def rag_process():
    data = request.json
    all_text = data["all_text"]
    query = data["query"]
    result = rag_method(all_text, query, logfile)
    return json.dumps(result)


@app.route('/easyocr', methods=['POST'])
def easyocr_process():
    try:
        # image = request.files.get("file")
        process_logger("EASY OCR", logfile)
        data = request.json
        base64File = data["base64"]
        format = data["format"]
        result = ocr_method(base64File, format, logfile)
        return result
    except Exception as e:
        log_exception("EasyOcr_APP", logfile)
        return {
            "error": str(e),
            "success": False
        }, 500


@app.route('/download_edit_pdf', methods=['POST'])
def download_edit_pdf():
    try:
        process_logger("DOWNLOAD EDIT PDF", logfile)
        data = request.json
        output_path = data["output_path"]
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True)
        else:
            return "file not found"
    except Exception as e:
        log_exception("download_edit_pdf", logfile)
        return {
            "error": str(e),
            "success": False
        }, 500


@app.route('/make_editable_pdf', methods=['POST'])
def make_editable_pdf():
    try:
        data = request.files
        file = data["file"]
        input_pdf_path = file.filename
        output_pdf_path = f"output_{file.filename}"
        file.save(input_pdf_path)
        coordinates = []
        if not wait_for_pdf_ready(input_pdf_path, len(fitz.open(input_pdf_path))):
            log_exception("PDF not ready for OCR", logfile)
            os.remove(input_pdf_path)
            return []
        add_text_to_pdf(input_pdf_path, output_pdf_path, coordinates, logfile)
        if os.path.exists(output_pdf_path):
            return send_file(output_pdf_path, as_attachment=True)
        else:
            return send_file(input_pdf_path, as_attachment=True)
    except:
        log_exception("make_editable_pdf", logfile)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

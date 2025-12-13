import os

os.environ["COLBERT_DISABLE_EXTENSIONS"] = "1"
os.environ["COLBERT_LOAD_TORCH_EXTENSION_VERBOSE"] = "0"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

from flask import Flask
import sys
from datetime import datetime

outputPath = os.getcwd()
logfile = os.path.join(outputPath, "hosting_log.txt")
app = Flask(__name__)
from ragatouille import RAGPretrainedModel
RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

# from sentence_transformers import SentenceTransformer
# RAG = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


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


@app.route('/rag_hosting', methods=['GET'])
def rag_hosting():
    try:
        return RAG
    except Exception as e:
        log_exception("rag_hosting:", logfile)
        return ""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

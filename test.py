
from ragatouille import RAGPretrainedModel

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0",use_faiss_gpu=False)

# import base64
# import json
# import io
#
# from PIL import Image
# config_data = json.loads(open("config.json").read())
# imgBase64_1 = config_data["pngBase64"]
# imgBase64 = config_data["imageBase64"]
# decoded_data = base64.b64decode(imgBase64_1)
# img=Image.open(io.BytesIO(decoded_data))
# print(img.format,img.filename)
# # with open(f"{img.filename}.{img.format}","wb")as f:
# #     f.write(byte64_Data)
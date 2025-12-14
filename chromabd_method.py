import chromadb
import json
import os
import sys
from datetime import datetime

config_data = json.loads(open("config.json", "r+").read())

collection_tableName = config_data["tableName"]


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


def get_chromdblist(logfile):
    try:
        return collectionTable,chroma_client
    except:
        log_exception("get_chromdblist", logfile)
        return {}


def chromadb_method(all_text, embeddings, fileName, uuidName, logfile):
    try:
        collectionTable.add(documents=[fileName], ids=[uuidName])
        index = 0
        print(collectionTable.get()['documents'])
        for doc in collectionTable.get()['documents']:
            if fileName == doc:
                # collectionTable.update(documents=[fileName],ids=[idsList for idsList in collectionTable.get(include=['documents'])]])
                print("TRUE")
                break
            index += 1

        isCreate = collectionTable.get()['ids'][index] in [chromaName.name for chromaName in
                                                           chroma_client.list_collections()]
        if isCreate:
            collectionIds = chroma_client.get_collection(name=collectionTable.get()['ids'][index])
        else:
            collectionIds = chroma_client.create_collection(name=collectionTable.get()['ids'][index])

        idsList = ["ids" + str(n) for n in range(len(all_text))]
        collectionIds.add(embeddings=embeddings, ids=idsList, documents=all_text)

        return collectionIds
    except:
        log_exception("chromadb_method:", logfile)

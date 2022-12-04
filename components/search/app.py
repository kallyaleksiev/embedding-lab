import os

from flask import Flask, request, jsonify
import numpy as np

import faiss

app = Flask(__name__)

INDEX_PATH = "indexes/article_index.npy"
IDS_DICT_PATH = "indexes/ids_dict.npy"

article_index = faiss.deserialize_index(np.load(INDEX_PATH, allow_pickle=True))
content_ids_dict = np.load(IDS_DICT_PATH, allow_pickle=True).item()

NPROBE = int(os.environ.get("NPROBE", "10"))
SEARCH_K = int(os.environ.get("SEARCH_K", "10"))

@app.route("/search", methods=["POST"])
def search():
    if not request.is_json:
        return "Data must be JSON!", 400
    
    req_json = request.get_json()
    embedding_np = np.array(req_json.get("embedding"))

    article_index.nprobe = NPROBE
    _, Ids = article_index.search(embedding_np, k=SEARCH_K)
    
    content_ids = [content_ids_dict.get(int_id, "N/A") for int_id in Ids[0, :]]
    resp_json = {"ids": content_ids}

    return jsonify(resp_json)
    
    
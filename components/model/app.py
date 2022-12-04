import os

from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModel

from utils import extract_embedding

app = Flask(__name__)

LOCAL_PATH_TO_MODEL = "model_data"
tokenizer = AutoTokenizer.from_pretrained(LOCAL_PATH_TO_MODEL)
model = AutoModel.from_pretrained(LOCAL_PATH_TO_MODEL)

@app.route("/")
def hey_you():
    return "<p>Hey you</p>"

@app.route("/embed", methods=["POST"])
def apply():
    if not request.is_json:
        return "Data must be JSON!", 400
    
    req_json = request.get_json()
    title = req_json.get("title", None)
    if not title:
        return "You must send a title!", 400

    tokenized_title = tokenizer(title,
                                padding=True,
                                truncation=True,
                                return_tensors="pt",
                                )
    outs = model(**tokenized_title)
    title_embedding = extract_embedding(outs, tokenized_title)
    title_embedding_np = title_embedding.detach().numpy()

    # TODO: Serialize better
    resp_json = {
        "embedding": title_embedding_np.tolist()
    }
    return jsonify(resp_json)
    
    
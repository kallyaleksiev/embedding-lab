import os

from flask import Flask, request
import redis
import requests

import checker

app = Flask(__name__)

# configure connection to Redis
REDIS_HOSTNAME = os.environ.get("REDIS_HOSTNAME", "arachne-redis-service")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_PORT = 6379

# model pods configuration
MODEL_PORT = 8080

# faiss pod configuration
SEARCH_HOST = os.environ.get("SEARCH_HOST", "arachne-search-service")
SEARCH_PORT = 8080

try:
    if REDIS_PASSWORD is not None:
        redis_server = redis.StrictRedis(host=REDIS_HOSTNAME,
                                         port=REDIS_PORT,
                                         password=REDIS_PASSWORD,
                                         )
    else:
        redis_server = redis.Redis(host=REDIS_HOSTNAME,
                                   port=REDIS_PORT,
                                   )
except redis.ConnectionError as e:
    app.logger.error("Could not connect to Redis, this is quite fatal")
    raise e

app.logger.info("Connected to Redis OK")


@app.route("/")
def hey_you():
    return "<p>Hey you</p>"

# apply a model and return the corresponding
# final-layer activation (embedding)
@app.route("/apply/<model_name>", methods=["POST"])
def apply(model_name):
    if not checker.is_alphanumeric_lowercase_nonempty(model_name):
        return "<p>What an unreasonable request! Try a valid model name!</p>", 400

    service_bytes = redis_server.get(model_name)
    if not service_bytes:
        return "<p>No such model present!</p>", 400

    if not request.is_json:
        return "<p> Bad Request! Can only accept JSON!</p>", 400

    req_json = request.get_json()
    title = req_json.get("title", None)

    if title is None:
        return "<p> Bad Request! Must provide title!</p>", 400

    service_hostname = service_bytes.decode("utf-8")

    model_url = f"http://{service_hostname}:{MODEL_PORT}/embed"
    payload = {"title": title}
    headers = {"Content-Type": "application/json"}

    response = requests.request(method="POST",
                                url=model_url,
                                json=payload,
                                headers=headers,
                                )
    embedding = response.json().get("embedding")
    return {
        "embedding": embedding
    }

# apply a model and also search with it using search
@app.route("/searchwith/<model_name>", methods=["POST"])
def searchwith(model_name):
    if not checker.is_alphanumeric_lowercase_nonempty(model_name):
        return "<p>What an unreasonable request! Try a valid model name!</p>", 400

    service_bytes = redis_server.get(model_name)
    if not service_bytes:
        return "<p>No such model present!</p>", 400

    if not request.is_json:
        return "<p> Bad Request! Can only accept JSON!</p>", 400

    req_json = request.get_json()
    title = req_json.get("title", None)

    if title is None:
        return "<p> Bad Request! Must provide title!</p>", 400

    service_hostname = service_bytes.decode("utf-8")

    model_url = f"http://{service_hostname}:{MODEL_PORT}/embed"
    payload = {"title": title}
    headers = {"Content-Type": "application/json"}

    response = requests.request(method="POST",
                                url=model_url,
                                json=payload,
                                headers=headers,
                                )
    embedding = response.json().get("embedding")

    search_url = f"http://{SEARCH_HOST}:{SEARCH_PORT}/search"
    search_payload = {"embedding": embedding}

    response = requests.request(method="POST",
                                url=search_url,
                                json=search_payload,
                                headers=headers,
                                )
    content_ids = response.json().get("ids")
    return {
        "ids": content_ids
    }

# register a model to the cluster
@app.route("/push", methods=["POST"])
def push():
    if not request.is_json:
        return "<p> Bad Request! Can only accept JSON!</p>", 400

    req_json = request.get_json()
    new_model_name = req_json.get("modelName", "")
    if not new_model_name:
        return "<p>Model name cannot be empty!</p>", 400

    if not checker.is_alphanumeric_lowercase_nonempty(new_model_name):
        return "<p>What an unreasonable request! Try a valid model name!</p>", 400

    redis_server.set(new_model_name, f"arachne-{new_model_name}-model-service")
    return {
        "set": new_model_name
    }

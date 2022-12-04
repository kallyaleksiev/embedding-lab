# arachne

This project is an "embedding lab" running as a kubernetes cluster. The idea is to allow you to conveniently obtain embeddings of documents via a REST API and search for closest matches usign the [faiss](https://github.com/facebookresearch/faiss) library. 

It build several docker containers that expose endpoints on which model inference and search can be performed. It then combines those containers and deploys them in a kubernetes cluster. As a POC here, the `kind` [Kubernetes in Docker](https://kind.sigs.k8s.io) tool is used but the cluster itself can easily be run on AWS or Azure.

The way it works is that you set it up and then use the `tool.py` to push new models that do embeddings from the huggingface hub on to the cluster. This allows you to test the quality of embeddings returned by various different models in a streamlined and convenient manner. The models need to do 384-dimensional embeddings. In addition, if you want to use the `faiss` search function, you need to precompute your index and add it to a `components/search.indexes` directory, along with a dictionary mapping faiss ids to document ids that are meaningful to the specific use case. 

## Prerequisites

|     PACKAGE           |   DESCRIPTION                                             |
|-----------------------|-----------------------------------------------------------|
|   `kind`              |  Tool that allows you to run kubernetes in docker locally |
|   `kubernetes` CLI    |  To control the cluster                                   |
|   `docker`     CLI    |  To build and distribute images                           |


## Contents

|     FILE/FOLDER       |   DESCRIPTION                                            |
|-----------------------|----------------------------------------------------------|
|   `components`        |  Blueprints for the various deployments int he cluster   |
|   `setup.sh`          |  Bash script to start up your cluster                    |
|   `tool.py`           |  Python tool to push models                              |
|   `requirements.txt`  |  List of python requirements                             |



## To run

0. Put your faiss index and ids mapping in the indexes subdirectory of the `components/search` directory so they get build with the search container.

1. Run `python3 -m venv venv` to create a virtual environment.

2. (On Linux and MacOS) Activate the environment by running `source venv/bin/activate`.

3. Run `./setup.sh` to create your cluster using `kind`. On linux you might want to run it with the `-l` option to also setup a LoadBalancer. On MacOS, you have to find another way to expose your local cluster, because docker by deafult does not expose the docker network to the host. One simple option is to run `kubectl proxy --port 8080` in a separate terminal. This will start a proxy for your K8s API server, so that your resources will be available at a URL of the form: "http://127.0.0.1:8080/api/v1/namespaces/" + "namespace name" + "services" + "service-name:service-port" + proxy, i.e. in our case "http://127.0.0.1:8080/api/v1/namespaces/default/services/arachne-gateway-service:8080/proxy"

***NOTE:*** The proxy is only for debugging and local testing purposes, it should not be used in production scenarios.

4. Run `./tool.py` with the proper model names you need to push new models to your cluser (for example something like `./tool.py --huggingface-name sentence-transformers/all-MiniLM-L6-v2 --pod-name sentencebert`)

5. Use requests like the following to interact with your cluster:

- To retrieve the closest matching titles from your index: 

`curl -X POST "$GATEWAY/searchwith/$MODEL_NAME" -H 'Content-Type: application/json' -d '{"title": "$TITLE"}'`

- To get the embedding of a title:

`curl -X POST "$GATEWAY/apply/$MODEL_NAME" -H 'Content-Type: application/json' -d '{"title": "$TITLE"}'`
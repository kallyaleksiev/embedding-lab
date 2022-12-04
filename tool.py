#!./venv/bin/python
import argparse
import logging
import tempfile
import os
import shutil
import subprocess
import yaml

import requests
from kubernetes import client as k8s_client, config as k8s_config, utils as k8s_utils
from transformers import AutoTokenizer, AutoModel

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%m/%d/%Y %I:%M:%S %p",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="arachne", description="Script for pushing models to cluster")

    parser.add_argument("--huggingface-name",
                        type=str,
                        help="HuggingFace name of model to push to cluster")

    parser.add_argument("--pod-name",
                        type=str,
                        help="The name of the model as you want to appear in the cluster")

    args = parser.parse_args()

    GATEWAY_URL = os.environ.get("GATEWAY_URL", None)
    if GATEWAY_URL is None:
        logger.warning(
            "GATEWAY_URL environment variable is not set, defaulting to localhost at 8080 proxy setup")
        GATEWAY_URL = "http://127.0.0.1:8080/api/v1/namespaces/default/services/arachne-gateway-service:8080/proxy"

    REGISTRY = os.environ.get("REGISTRY", None)
    if REGISTRY is None:
        logger.warning(
            "REGISTRY environment variable is not set, defaulting to localhost:8000")
        REGISTRY = "localhost:8000"

    # create temporary directory to use as context to build dokcker image
    # use the components/model one as template
    with tempfile.TemporaryDirectory() as tempdir:
        components_dir = os.path.join(os.getcwd(), "components/model")

        model_app_file = os.path.join(components_dir, "app.py")
        model_utils_file = os.path.join(components_dir, "utils.py")
        model_dockerfile_file = os.path.join(components_dir, "Dockerfile")
        model_requirements_file = os.path.join(
            components_dir, "requirements.txt")

        for component_filename in [model_app_file, model_utils_file, model_dockerfile_file, model_requirements_file]:
            shutil.copy(component_filename, tempdir)

        # download the model to the directory
        model_data_dir = os.path.join(tempdir, "model_data")
        tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=args.huggingface_name,
                                                  cache_dir=tempdir)
        model = AutoModel.from_pretrained(
            pretrained_model_name_or_path=args.huggingface_name, cache_dir=tempdir)

        tokenizer.save_pretrained(model_data_dir)
        model.save_pretrained(model_data_dir)

        # build model image and push to the registry
        model_image_tag = f"{REGISTRY}/{args.pod_name}:v0"
        subprocess.run(
            ["docker", "build", "-t", f"{model_image_tag}", tempdir])
        subprocess.run(["docker", "push", model_image_tag])

    # edit model configuration and deploy to cluster
    model_deployment_yaml_file = os.path.join(
        components_dir, "model-deployment.yaml")
    model_service_yaml_file = os.path.join(
        components_dir, "model-service.yaml")
    k8s_config.load_kube_config()

    with open(model_deployment_yaml_file, "r") as depl_f, open(model_service_yaml_file, "r") as ser_f:
        depl_dict = yaml.safe_load(depl_f)
        ser_dict = yaml.safe_load(ser_f)

        depl_dict["metadata"]["name"] = f"arachne-{args.pod_name}-model-deployment"
        depl_dict["spec"]["template"]["spec"]["containers"][0]["image"] = model_image_tag

        ser_dict["metadata"]["name"] = f"arachne-{args.pod_name}-model-service"

        v1_client = k8s_client.ApiClient()
        k8s_utils.create_from_dict(v1_client, depl_dict)
        k8s_utils.create_from_dict(v1_client, ser_dict)

    # register model name to cluster
    data = {
        "modelName": args.pod_name
    }
    headers = {
        "Content-Type": "application/json"
    }
    requests.request(
        "PUT", url=f"{GATEWAY_URL}/push", headers=headers, json=data)

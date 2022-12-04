#!/bin/bash
set -e

while getopts 'r:c:p:l' opt; do
  case "$opt" in
    r)
      registryname="$OPTARG"
      ;;

    c)
      clustername="$OPTARG";
      ;;

    p)
      registryport="$OPTARG";
      ;;
   
    l)
      loadbalancing=True
      ;;
    
    *)
      echo "Usage: $(basename "$0") [-r REGISTRYNAME] [-c CLUSTERNAME] [-p REGISTRYPORT] [-l]"
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"

if [[ -z ${registryname+x} ]]; then registryname="registry"; fi

if [[ -z ${clustername+x} ]]; then clustername="kindcluster"; fi

if [[ -z ${registryport+x} ]]; then registryport="8000"; fi

if [[ -z ${loadbalancing+x} ]]; then loadbalancing=False; fi

registryrunning="$(docker inspect -f "{{.State.Running}}" "${registryname}" 2>/dev/null || true)"

if [[ ! "$registryrunning" == "true" ]]; then 
    echo "Setting up local registry..."
    docker run -d -p "127.0.0.1:$registryport:5000" --name "$registryname" --restart=always registry:2;
else
    echo "Registry already running..."
fi

# setup kind cluster
echo "Setting up kind cluster..."
cat <<EOF | kind create cluster --name $clustername --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:${registryport}"]
    endpoint = ["http://${registryname}:5000"]
nodes:
    - role: control-plane
    - role: worker
    - role: worker
EOF

# Part of agreed best practice for setting up a cluster that 
# pulls from a local registry. More details at the following:
# https://github.com/kubernetes/enhancements/tree/master/keps/sig-cluster-lifecycle/generic/1755-communicating-a-local-registry
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${registryport}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

# connect registry to the same network as the cluster 
echo "Connecting registry to kind network..."
registryconnected="$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' "${registryname}")"
echo "$registryconnected"
if [ "$registryconnected" == "null" ]; then
  docker network connect "kind" $registryname
fi

# set-up load balancer (optional as this is not the only way to 
# access the cluster from the outside, e.g. NodePort or enabling 
# a proxy for a ClusterIP Service are also options. The LoadBalancer
# set-up is inspired by https://kind.sigs.k8s.io/docs/user/loadbalancer/
if [[ "$loadbalancing" == "True" ]] ; then 
    echo "Setting up Metallb LoadBalancer at default..."
    kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.7/config/manifests/metallb-native.yaml

    kubectl wait --namespace metallb-system --for=condition=ready pod --selector=app=metallb --timeout=90s

    # get cidr range of kind network
    range="$(docker network inspect -f '{{.IPAM.Config}}' kind | cut -b 3-8)"
    cat <<EOF | kubectl apply -f -
    apiVersion: metallb.io/v1beta1
    kind: IPAddressPool
    metadata:
        name: example
        namespace: metallb-system
    spec:
        addresses:
        - ${range}.255.200-${range}.255.250
EOF

    cat <<EOF | kubectl apply -f -
    apiVersion: metallb.io/v1beta1
    kind: L2Advertisement
    metadata:
        name: empty
        namespace: metallb-system
EOF

fi

# build the gateway container and push to regsitry
echo "Building gateway..."
docker build -t gateway:v0 components/gateway
docker tag gateway:v0 localhost:${registryport}/gateway:v0
docker push localhost:${registryport}/gateway:v0

# build the redis container and push to regsitry
echo "Building redis..."
docker build -t redis:v0 components/redis
docker tag redis:v0 localhost:${registryport}/redis:v0
docker push localhost:${registryport}/redis:v0

# build the search container and push to regsitry
echo "Building search..."
docker build -t search:v0 components/search
docker tag search:v0 localhost:${registryport}/search:v0
docker push localhost:${registryport}/search:v0

# create the needed pods
echo "Applying arache.yaml ..."
port=$registryport envsubst < components/arachne.yaml | kubectl apply -f -

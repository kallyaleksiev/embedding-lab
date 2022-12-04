# syntax=docker/dockerfile:1 
FROM ubuntu:22.04

ARG TARGET_DIR="/app"
ARG CONDA_URL="https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh"

WORKDIR ${TARGET_DIR}

RUN apt update

# make sure that we have python but it's python3
RUN apt install -y python3-pip python-is-python3

# get wget (to then get conda)
RUN apt install -y wget

# get conda (because it is the recommended and apparently
# least frictious way isntall faiss) conda introduces some
# problems but it is the easiest and most streamlined way 
# to install faiss 
ENV CONDA_DIR /opt/conda
RUN wget $CONDA_URL -O conda.sh
RUN bash conda.sh -b -p $CONDA_DIR 
RUN rm conda.sh
ENV PATH=$CONDA_DIR/bin:$PATH

# install faiss
RUN conda install -c pytorch faiss-cpu

COPY requirements.txt  .
RUN  python -m pip install -r requirements.txt

# TODO: Put your indexes in this indexes directory so 
# they get copied with the container
COPY indexes indexes/

COPY app.py .

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
        
# syntax=docker/dockerfile:1 
FROM python:slim-buster

# set the working directory - everything will subsequently 
# be executed inside this directory
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt
# to be able to run a model
RUN mkdir model_data
COPY model_data/ model_data
# copy the rest of the contents
COPY . .

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
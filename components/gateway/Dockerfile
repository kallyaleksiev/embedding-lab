# syntax=docker/dockerfile:1 
FROM python:slim-buster

# set the working directory - everything will subsequently 
# be executed inside this directory
WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
FROM python:3.8

WORKDIR /usr/src/bot

RUN apt-get install -y git

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src/ .

CMD [ "python", "-u", "main.py" ]

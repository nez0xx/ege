FROM python:3.12.3

WORKDIR /home/chatbot

COPY requirements.txt .

RUN pip3.12 install -r requirements.txt

COPY . ./

ENV PYTHONPATH=/home/chatbot

CMD python -m bot.main
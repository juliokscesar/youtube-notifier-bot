FROM python:3.11
WORKDIR /furry-bot
COPY requirements.txt /furry-bot/
RUN pip install -r requirements.txt
COPY . /furry-bot
CMD python furry_bot.py
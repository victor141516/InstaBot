FROM python:3-alpine
WORKDIR /app
RUN apk add --no-cache gcc python3-dev py3-pip musl-dev
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY . /app
WORKDIR /app
CMD [ "python3", "main.py" ]

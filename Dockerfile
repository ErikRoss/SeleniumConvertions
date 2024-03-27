FROM python:3.11-slim-buster
LABEL maintainer="bezheve@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR app/

COPY requirements.txt requirements.txt

RUN apt-get update \
    && apt-get install -y libpq-dev gcc

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

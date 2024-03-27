import os
import time

import requests
from celery import Celery
from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()
celery = Celery(
    "tasks",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
)


class RequestData(BaseModel):
    url: str
    params: dict
    user_agent: str
    timeout: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/",
                    "params": {"page": 1, "limit": 10},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "timeout": 1,
                }
            ]
        }
    }


@celery.task
def task_selenium(url: str, params: dict, user_agent: str, timeout: int):
    target_url = (
        url + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
    )
    try:
        status = requests.get(target_url)
        if status.status_code == 404:
            raise Exception(f"Status 404 ({target_url}) FAILED TO CONNECT")

        options = Options()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Remote(
            "http://webdriver:9515",
            options=options,
        )

        # driver = webdriver.Chrome(options=options)
        driver.get(target_url)
        page_loaded = driver.execute_script("return document.readyState")

        times = 0
        while page_loaded != "complete":
            times += 1
            if times == 600:
                raise Exception("The page is not loading")
            time.sleep(0.25)

        print("The page has loaded.")
        time.sleep(timeout)

        driver.quit()
        return "Done"

    except Exception as e:
        return f"ERROR: {e}"


@app.post("/selenium/")
async def selenium(data: RequestData):
    task_selenium.delay(data.url, data.params, data.user_agent, data.timeout)
    return {
        "message": "Tasks in process. Status look here: http://localhost:5555/task/"
    }


@app.get("/hello/")
async def say_hello():
    return {"message": "Hello world"}

from fastapi import FastAPI, HTTPException
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

BAMBOO_SUBDOMAIN = os.getenv("BAMBOOHR_SUBDOMAIN")
BAMBOO_API_KEY = os.getenv("BAMBOOHR_API_KEY")


@app.get("/")
def root():
    return {"message": "GRC Integration Service Running 🚀"}


@app.get("/integrations/bamboohr/test")
def test_connection():
    url = f"https://api.bamboohr.com/api/gateway.php/{BAMBOO_SUBDOMAIN}/v1/meta/users"

    response = requests.get(
        url,
        auth=(BAMBOO_API_KEY, "x"),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=response.text)

    return response.json()


@app.get("/integrations/bamboohr/employees")
def fetch_employees():
    url = f"https://api.bamboohr.com/api/gateway.php/{BAMBOO_SUBDOMAIN}/v1/reports/custom"

    payload = {
        "fields": [
            "id",
            "firstName",
            "lastName",
            "workEmail",
            "department",
            "jobTitle",
            "location",
            "division",
            "supervisor"
        ]
    }

    response = requests.post(
        url,
        json=payload,
        auth=(BAMBOO_API_KEY, "x"),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=response.text)

    return response.json()

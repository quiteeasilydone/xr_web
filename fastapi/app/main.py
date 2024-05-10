from fastapi import FastAPI
from app_fastapi import app
from uvicorn import run

if __name__ == "__main__":
    run(app, host='0.0.0.0', port=80)

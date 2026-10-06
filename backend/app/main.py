from fastapi import FastAPI

from app.api.applications import router as applications_router
from app.api.webhook import router as webhook_router

app = FastAPI(
    title="JobTrack API",
)

app.include_router(applications_router)
app.include_router(webhook_router)



@app.get("/")
def root():
    return {"message": "JobTrack API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
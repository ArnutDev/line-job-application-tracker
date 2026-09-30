from fastapi import FastAPI

from app.api.applications import router as applications_router

app = FastAPI(
    title="JobTrack API",
)

app.include_router(applications_router)


@app.get("/")
def root():
    return {"message": "JobTrack API is running"}
from fastapi import FastAPI

app = FastAPI(title="ApplyTrack API")


@app.get("/")
def root():
    return {"message": "ApplyTrack API is running"}
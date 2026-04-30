from fastapi import FastAPI

app = FastAPI(
    title="AI Research Assistant"
)


@app.get("/")
async def root():
    return {"message": "Backend Running"}
from fastapi import FastAPI

app = FastAPI(title="Tiny Inference")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Tiny Inference API", "status": "we are good it seems like"}

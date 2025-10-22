from fastapi import FastAPI

app = FastAPI()

print("lolol")


@app.get("/")
async def root():
    return "test"

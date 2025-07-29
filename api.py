from fastapi import FastAPI, Request
from pydantic import BaseModel
from deeppavlov import build_model, configs
import uvicorn

app = FastAPI()

# Load DeepPavlov model
model = build_model('deeppavlov_config.json', download=True)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    response = model([req.message])
    return {"response": response[0]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
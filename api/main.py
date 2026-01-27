import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ai_routes import router as ai_router
from routes.tts_routes import router as tts_router
from routes.health_routes import router as health_router
from routes import image

app = FastAPI(title="Voicera API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router, prefix="/api")
app.include_router(tts_router, prefix="/api")
app.include_router(health_router)
app.include_router(image.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

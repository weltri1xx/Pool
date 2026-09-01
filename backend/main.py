from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.auth.controller import router as auth_router
from backend.post.controller import router as posts_router
# from backend.websocket.controller import router as websocket_router
# from backend.chat.controller import router as chat_router
# from backend.stories.controller import router as stories_router
# from backend.follows.controller import router as follows_router
from backend.database import Base, engine

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router)
app.include_router(posts_router)
# app.include_router(websocket_router)
# app.include_router(chat_router)
# app.include_router(stories_router)
# app.include_router(follows_router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
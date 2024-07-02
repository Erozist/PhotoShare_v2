import os
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter


from src.database.db import get_db
from src.routes import  auth, users, photos, comments, posts
from src.conf.config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    r = await redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(r)
    yield
    await r.close()

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = Path(__file__).parent
directory = BASE_DIR.joinpath("src").joinpath("static")
app.mount("/static", StaticFiles(directory=directory), name="static")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(photos.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(posts.router, prefix="/api")

templates = Jinja2Templates(directory=BASE_DIR / "src" / "templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    The index function renders the index.html template and returns it as an HTML response.

    :param request: Request: The incoming HTTP request
    :return: A TemplateResponse object containing the rendered HTML template
    :doc-author: Trelent
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "our": "Build group"}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), log_level="info")
    
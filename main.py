# to run :: python -m uvicorn main:app --reload
from fastapi import FastAPI, requests
from fastapi.middleware.cors import CORSMiddleware
import time
from database import Base, engine
from routers import conversations, chat, users


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Chat API",
    description="A simple API for AI-powered chat applications",
    version="1.0.0"
)

@app.middleware("http")
async def add_process_time_header(request: requests.Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Chat API!"}

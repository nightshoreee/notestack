"""
Step 1 entry point: just enough to prove the server boots and the DB
connects. Routers (auth, courses, lectures, roadmap, study-room) get
included here in later steps as they're built.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models  # noqa: F401 — forces all model modules to register on Base before create_all
from routers import auth, courses, lectures, roadmap, study_room
from schemas.user_schema import UserOut
from utils.auth_utils import get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PeerNotes API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(lectures.router)
app.include_router(roadmap.router)
app.include_router(study_room.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "PeerNotes API", "step": "13 - full backend complete, end-to-end tested"}


@app.get("/me", response_model=UserOut)
def read_current_user(current_user=Depends(get_current_user)):
    """Protected test route — proves JWT verification works end to end."""
    return current_user


@app.get("/health")
def health_check():
    return {"status": "healthy"}

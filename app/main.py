from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
import os
import io
import redis
from rq import Queue
from sqlalchemy.orm import Session

from .database import get_db, engine, Base
from . import models
from . import tasks

FS_PATH = "./fs/"

os.makedirs(FS_PATH, exist_ok=True)

app = FastAPI()

redis_conn = redis.Redis()
q = Queue(connection=redis_conn)

ROLE = os.environ.get("ROLE", "generator")

if ROLE == "generator":
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    @app.get("/images")
    def images_get(db: Session = Depends(get_db)):
        images = db.query(models.Image).all()
        return [{"id": img.id, "filename": img.filename} for img in images]

    @app.post("/image")
    async def image_post(file: UploadFile = File(...)):
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        contents = await file.read()
        job = q.enqueue(tasks.generate_mods, io.BytesIO(contents), file.filename)
        return {"job_id": job.get_id()}

elif ROLE == "verifier":
    @app.post("/verify")
    def verify():
        job = q.enqueue(tasks.verify_mods)
        return {"job_id": job.get_id()}
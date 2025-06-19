from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
import random
import os
import io
import uuid
import asyncio
import redis
from rq import Queue
from sqlalchemy.orm import Session
from PIL import Image

from database import get_db, engine, Base
import models
import tasks

FS_PATH = "./fs/"
NUM_MODIFIED_IMAGES = 1 # 100
NUM_MODIFICATIONS_MIN = 100

os.makedirs(FS_PATH, exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

redis_conn = redis.Redis()
q = Queue(connection=redis_conn)

@app.get("/images")
def images_get(db: Session = Depends(get_db)):
    images = db.query(models.Image).all()
    return [{"id": img.id, "filename": img.filename} for img in images]

@app.post("/image")
async def image_post(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    contents = await file.read()
    job = q.enqueue(tasks.add_image, io.BytesIO(contents), file.filename)
    return {"job_id": job.get_id()}

@app.post("/check")
def check():
    job = q.enqueue(tasks.check_mods)
    return {"job_id": job.get_id()}
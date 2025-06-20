import json
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import io
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app import models, tasks, config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],  # Or set to specific domains in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_conn = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
q = Queue(connection=redis_conn)

ROLE = os.environ.get("ROLE", "generator")

@app.get(
    "/status/{job_id}",
    summary="Get background job status",
    description="Retrieve the status and progress of a background job by its ID. Returns the job status, result if finished, and progress information if available.",
    response_description="A dictionary containing the job status, result (if finished), and progress (if available)."
)
def get_status(job_id: str):
    job = q.fetch_job(job_id)
    if not job:
        return {"status": "not found"}
    
    job_status = {}

    if job.is_finished:
        job_status = {"status": "finished", "result": job.result}
    elif job.is_failed:
        job_status = {"status": "failed"}
    else:
        job_status = {"status": "in progress"}

    val = redis_conn.get(f"progress:{job_id}")
    if val:
        job_status["progress"] = json.loads(val)

    return job_status

if ROLE == "generator":
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    @app.get("/images")
    def images_get(db: Session = Depends(get_db)):
        images = db.query(models.Image).all()
        return [{"id": img.id, "filename": img.filename} for img in images]

    @app.post(
        "/image",
        summary="Upload an image for modification",
        description="Handles image file uploads for modification. Only image files are allowed. Returns a job ID for tracking.",
        response_description="A dictionary containing the job ID of the enqueued background task."
    )
    async def image_post(file: UploadFile = File(...)):
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        contents = await file.read()
        job = q.enqueue(tasks.generate_mods, io.BytesIO(contents), file.filename)
        return {"job_id": job.get_id()}

elif ROLE == "verifier":
    @app.post(
        "/verify",
        summary="Start verification of modifications",
        description="Enqueues a background job to verify modifications. Returns a job ID for tracking.",
        response_description="A dictionary containing the job ID of the enqueued verification task."
    )
    def verify():
        job = q.enqueue(tasks.verify_mods)
        return {"job_id": job.get_id()}
    
    @app.get(
        "/modifications",
        summary="Retrieve modification records",
        description="Retrieve a list of up to 100 modification records from the database. Each record includes its ID, filename, and verification status.",
        response_description="A list of modification records with their ID, filename, and verification status."
    )
    def get_modifications(db: Session = Depends(get_db)):
        modifications = db.query(models.Modification).limit(100).all()
        return [{"id": mod.id, "filename": mod.filename, "status": mod.verification} for mod in modifications]
import os
from rq import Worker
from redis import Redis
from app.config import REDIS_HOST, REDIS_PORT, FS_PATH

# Connect to Redis
conn = Redis(host=REDIS_HOST, port=REDIS_PORT)

# Create and start the worker
if __name__ == '__main__':
    # Ensure the file system path exists
    os.makedirs(FS_PATH, exist_ok=True)
    
    worker = Worker(queues=['default'], connection=conn)
    worker.work()
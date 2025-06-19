from rq import Worker
from redis import Redis

# Connect to Redis
conn = Redis()

# Create and start the worker
if __name__ == '__main__':
    worker = Worker(queues=['default'], connection=conn)
    worker.work()
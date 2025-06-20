import os

FS_PATH = "./fs/"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ligence:pass@localhost/hw")

NUM_MODIFIED_IMAGES = 100
NUM_MODIFICATIONS_MIN = 100
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "yarntales")
SECRET_KEY = os.getenv("SECRET_KEY")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is required in backend/.env")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required in backend/.env")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
)
db = client[MONGO_DB_NAME]

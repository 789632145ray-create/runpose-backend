"""MongoDB 連線（本機 / Atlas / Railway 容器共用）。"""

from __future__ import annotations

import os

import certifi
from pymongo import MongoClient


def make_mongo_client(url: str | None = None, timeout_ms: int = 15_000) -> MongoClient:
    mongo_url = url or os.environ.get("POSE_MONGO_URL", "mongodb://localhost:27017")
    kwargs: dict = {
        "serverSelectionTimeoutMS": timeout_ms,
        "connectTimeoutMS": timeout_ms,
        "socketTimeoutMS": 60_000,
    }
    # Docker / Railway 容器需指定 CA，否則 Atlas 常出現 SSL handshake failed。
    if mongo_url.startswith("mongodb+srv://") or "tls=true" in mongo_url.lower():
        kwargs["tlsCAFile"] = certifi.where()
    return MongoClient(mongo_url, **kwargs)

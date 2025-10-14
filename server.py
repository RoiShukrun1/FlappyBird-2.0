# server.py
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
import os
import time  
import bcrypt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo import DESCENDING  

MONGO_URI = "mongodb+srv://FlappyBird:2XVyaNW0oBQGXL7I@flappybird.ppmtljv.mongodb.net/?retryWrites=true&w=majority&appName=FlappyBird"
DB_NAME = "flappybird"
USERS_COLL = "users"
LEADERBOARD_COLL = "leaderboard"  

if not MONGO_URI:
    raise RuntimeError("Set MONGO_URI env var to your MongoDB connection string.")

app = FastAPI()

# One warm Mongo client (connection pooling)
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db[USERS_COLL]
users.create_index("username_lower", unique=True)

# leaderboard 
leaderboard = db[LEADERBOARD_COLL]
leaderboard.create_index([("score", DESCENDING), ("ts", DESCENDING)])

class Creds(BaseModel):
    username: str
    password: str

class SubmitScore(BaseModel):
    name: str
    score: int

@app.get("/health")
def health():
    client.admin.command("ping")
    return {"ok": True}

@app.post("/register")
def register(c: Creds):
    uname = (c.username or "").strip()
    print(f"Register: '{uname}'")
    if not c.password or len(c.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    try:
        pw_hash = bcrypt.hashpw(c.password.encode(), bcrypt.gensalt()).decode()
        users.insert_one({
            "username": uname,
            "username_lower": uname.lower(),
            "password_hash": pw_hash,
            "best_score": 0
        })
        return {"ok": True}
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="This username is already taken.")

@app.post("/login")
def login(c: Creds):
    uname = (c.username or "").strip()
    u = users.find_one({"username_lower": uname.lower()})
    if not u:
        raise HTTPException(status_code=404, detail="No account found with that username.")
    hashed = u.get("password_hash")
    if isinstance(hashed, str):
        hashed = hashed.encode()
    if not hashed or not bcrypt.checkpw(c.password.encode(), hashed):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    # Return public fields only
    return {"ok": True, "user": {"username": u["username"], "best_score": u.get("best_score", 0)}}


@app.get("/user/best")
def user_best(username: str):
    """Return best score for a given username (or None if not found)."""
    u = users.find_one({"username_lower": (username or "").lower()})
    if not u:
        return {"ok": False, "best": None}
    return {"ok": True, "best": int(u.get("best_score", 0))}

@app.post("/leaderboard/submit")
def leaderboard_submit(body: SubmitScore):
    """
    Insert a score row; update user's best_score if user exists.
    Returns: { ok, id, rank }
    """
    name = (body.name or "Player").strip() or "Player"
    score = int(body.score)

    # insert row
    doc = {"name": name, "score": score, "ts": int(time.time())}
    res = leaderboard.insert_one(doc)

    # cheap rank estimate: count strictly higher scores
    higher = leaderboard.count_documents({"score": {"$gt": score}})
    rank = higher + 1

    # update user's best if present
    users.update_one(
        {"username_lower": name.lower()},
        {"$max": {"best_score": score}}
    )

    return {"ok": True, "id": str(res.inserted_id), "rank": rank}

@app.get("/leaderboard/top")
def leaderboard_top(limit: int = 10):
    """
    Return Top-N rows (default 10). Client can ignore 'rank' if not shown.
    """
    limit = max(1, min(int(limit), 50))
    items = []
    for i, r in enumerate(
        leaderboard.find({}, {"name": 1, "score": 1})
                   .sort([("score", -1), ("ts", -1)])
                   .limit(limit),
        start=1
    ):
        items.append({
            "id": str(r["_id"]),
            "name": r.get("name", "Anonymous"),
            "score": int(r.get("score", 0)),
            "rank": i
        })
    return {"ok": True, "items": items}

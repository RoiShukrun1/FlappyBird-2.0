# 🐦 Flappy Bird 2.0 – AI & Multiplayer Edition

A modern take on **Flappy Bird** with:
- **Single player** classic mode
- **Man vs Machine** (human vs NEAT‑AI)
- **AI challenge** with difficulty levels: Easy / MEDIUM / HARD / EXTREME
- **Multiplayer LAN (host/client)** for online play
- **User registration & login** (bcrypt hashing)
- **Leaderboard** backed by MongoDB
- **AI player demonstration**

---

Traditional versions of casual games like *Flappy Bird* offer only a basic single‑player loop, which limits replayability and long‑term engagement. Most clones lack competitive elements, AI challenges, multiplayer, or social features. Players quickly lose interest without difficulty progression, variety, or learning opponents.

This project addresses those gaps by adding multiple game modes, AI‑powered opponents with configurable difficulty, real‑time multiplayer, and a competitive leaderboard. The result is a modern, feature‑rich experience designed to sustain player interest with diverse gameplay and social competition.

## Key features

1. Build a feature‑rich Flappy Bird with multiple modes (classic, AI challenge, Man‑vs‑Machine, multiplayer).
2. Implement NEAT‑based AI opponents with configurable difficulty (Easy/Medium/Hard/Extreme).
3. Provide real‑time multiplayer (host/client) for competitive play.
4. Add registration and login for personalized experiences.
5. Integrate a global leaderboard backed by MongoDB.
6. Include an AI demonstration/training flow to showcase learning over generations.

## 📦 Requirements (install once)
Install from the provided `requirements.txt`:
```bash
python -m pip install -r requirements.txt
```

If you prefer manual/global installs:
```bash
python -m pip install uvicorn requests pygame bcrypt fastapi pymongo neat-python
```

> **Python**: use 3.10+ (tested on 3.12/3.13). On Windows, ensure you run the same `python` you used to install packages:
> `where python` (PowerShell/CMD) and `python --version`.
---

## ▶️ Run the Backend (FastAPI + Uvicorn)
From the project root:
uvicorn server:app --host 127.0.0.1 --port 8001 --reload
---

## 🎮 Run Game Modes
Run it with Python and pick a mode:
- **Main menu**
  python main.py

## 👤 Author

Roi Shukrun, Aviel Segev, Kobi Hadad

## Acknowledgements
We would like to thank our course instructors and fellow students for their support and feedback throughout this project.

Happy coding!

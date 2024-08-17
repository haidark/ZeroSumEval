import os
import asyncio
import time
import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from huggingface_hub import Repository

from gradio_fastapi import gradio_lifespan_init
from glob import glob

import pandas as pd
import jsonlines
import json
import re


HF_TOKEN = os.environ.get("HF_TOKEN")
HF_REPO = os.environ.get("HF_REPO", "HishamYahya/zse-matches")
HF_USERNAME = os.environ.get("HF_USERNAME", "HishamYahya")
LOCAL_DIR = "zse-matches"
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "abc123")

app = FastAPI(lifespan=gradio_lifespan_init())


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the repository
repo = Repository(
    local_dir=LOCAL_DIR,
    clone_from=f"https://{HF_USERNAME}:{HF_TOKEN}@huggingface.co/datasets/{HF_REPO}",
)

async def update_local_repo():
    try:
        # Pull the latest changes
        repo.git_pull()
        print("Local repository updated successfully")
    except Exception as e:
        print(f"Failed to update local repository: {str(e)}")

@app.get("/api/leaderboard")
def get_leaderboard():
    leaderboard = dict()
    for leaderboard_path in glob(os.path.join(LOCAL_DIR, "games/*/leaderboard.csv")):
        game_name = leaderboard_path.split("/")[-2]
        leaderboard[game_name] = []
        df = pd.read_csv(leaderboard_path)
        for _, row in df.iterrows():
            # Append the row as a dictionary to the leaderboard with lowercase keys
            leaderboard[game_name].append({k.lower(): v for k, v in row.to_dict().items()})

    return leaderboard

@app.get("/api/models/{model_id}")
def get_model_matches(model_id: str):
    matches = []
    for match_path in glob(os.path.join(LOCAL_DIR, "games/*/matches/*")):
        # extract names and id. for example, gpt-4o2_vs_gpt-4o1_1723901983
        game_name = match_path.split("/")[-3]
        match_name = match_path.split("/")[-1]
        model_1, model_2, match_time = re.match(r"(.+)_vs_(.+)_(\d+)", match_name).groups()
        # convert to { id: 1, game: "Chess", opponent: "Model 2", result: "win", oldElo: 1500, newElo: 1515, eloDelta: 15, date: "2024-08-01" }
        if model_1 == model_id or model_2 == model_id:
            with open(os.path.join(match_path, "results.json")) as f:
                results = json.load(f)
            
            for result in results:
                results[result]["elos_delta"] = [int(x) for x in results[result]["elos_delta"]]
            
            match = {
                "id": match_path.split("/")[-1],
                "game": game_name,
                "opponent": model_2 if model_1 == model_id else model_1,
                "results": results,
                "timestamp": datetime.datetime.fromtimestamp(int(match_time)).strftime("%Y-%m-%d %H:%M:%S")
            }
            matches.append(match)
        
    return matches
        

@app.post("/api/webhook")
async def webhook(request: Request):
    payload = await request.json()

    # Verify the webhook secret
    if request.headers.get("X-Webhook-Secret") != WEBHOOK_SECRET:
        raise HTTPException("Invalid webhook secret")
    
    # Check if the webhook is for an update event
    if payload.get("event").get("action") == "update":
        # print with formatted time
        print(f"Update received at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        # Trigger the update process
        asyncio.create_task(update_local_repo())
        return {"message": "Update received, pulling latest changes"}
    
    return {"message": "Webhook received"}

@app.on_event("startup")
async def startup_event():
    # Ensure the repository is cloned on startup
    if not os.path.exists(os.path.join(LOCAL_DIR, ".git")):
        print("Cloning repository...")
        repo.clone()
    else:
        print("Repository already cloned, pulling latest changes...")
        await update_local_repo()

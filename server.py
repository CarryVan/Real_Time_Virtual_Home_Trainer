import asyncio
import logging
import os
import uuid
import time
import pickle
import sys
from datetime import datetime

import json
import cv2
import pose_module as pm
# from aiohttp import web
from av import VideoFrame
import uvicorn

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

#database
sys.path.append('./database')
import crud, models, schemas
from database import SessionLocal, engine
from schemas import SaveWorkout, SaveWorkoutSession
from sqlalchemy.orm import Session
from typing import List

from src.schemas import Offer, Info
from VideoTransformTrack import VideoTransformTrack, AudioTransformTrack, VideoTransformTrack2
from src.schemas import Offer, Live
ROOT = os.path.dirname(__file__)

#database connection
models.Base.metadata.create_all(bind=engine)
#database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/img", StaticFiles(directory="img"), name="img")
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger("pc")
pcs = set()

finish = False

@app.get("/", response_class=HTMLResponse)
async def pose_eatimation(request: Request):
    return templates.TemplateResponse("pose_estimation.html", {"request": request})


@app.get("/one.html", response_class=HTMLResponse)
async def one(request: Request):
    return templates.TemplateResponse("one.html", {"request": request})


@app.get("/schedule.html", response_class=HTMLResponse)
async def shcedule(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})

@app.get("/record.html", response_class=HTMLResponse)
async def record(request: Request):
    content = open(os.path.join(ROOT, f"templates/record.html"),
                   "r", encoding='UTF8').read()
    return templates.TemplateResponse("record.html", {"request": request})

@app.get("/pose_estimation.html", response_class=HTMLResponse)
async def record(request: Request):
    content = open(os.path.join(ROOT, f"templates/pose_estimation.html"),
                   "r", encoding='UTF8').read()
    return templates.TemplateResponse("pose_estimation.html", {"request": request})

@app.get("/start.html", response_class=HTMLResponse)
async def start(request: Request):
    content = open(os.path.join(ROOT, f"templates/start.html"),
                   "r", encoding='UTF8').read()
    return templates.TemplateResponse("start.html", {"request": request})

@app.get("/live.html", response_class=HTMLResponse)
async def live(request: Request):
    content = open(os.path.join(ROOT, f"templates/live.html"),
                   "r", encoding='UTF8').read()
    return templates.TemplateResponse("live.html", {"request": request})

@app.post("/offer")
async def offer(params: Offer):
    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)
    pc = RTCPeerConnection()
    

    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)
    
    player = MediaPlayer(os.path.join(ROOT, "workout_start.wav"))
    recorder = MediaBlackhole()
    

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        if track.kind == "audio":
            # pass
            pc.addTrack(player.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            global local_video
            local_video = VideoTransformTrack(
                track, exercise_list=params.exercise, cnt_list=params.cnt, set_list=params.set, breaktime_list=params.breaktime
            )
            pc.addTrack(local_video)
            recorder.addTrack(track)
        @track.on("ended")
        async def on_ended():
            await recorder.stop()
            coros = [pc.close() for pc in pcs]
            await asyncio.gather(*coros)
            pcs.clear()

    @pc.on("datachannel")
    def on_datachannel(channel):
        global local_video
        local_video.channel=channel
        @channel.on("message")
        def on_message(message):
            channel.send("msg")
    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

#database
@app.get("/one.html", response_class=HTMLResponse)
async def one(request: Request):
    return templates.TemplateResponse("one.html", {"request": request})

@app.post("/save_workout")
async def save_workout(params: Info, db: Session = Depends(get_db)):
    
    exercise = params.exercise.split(",")
    cnt = [int(x) for x in params.cnt.split(",")]
    set = [int(x) for x in params.set.split(",")]
    
    breaktime = [int(x) for x in params.breaktime.split(",")]

    most_recent = crud.get_recent_session(db)
    tot_len = len(exercise) + len(breaktime)

    crud.save_workout_session(db)

    for i in range(len(exercise)):
        sw = SaveWorkout
        sw.workout_session = int(most_recent.id) + 1
        sw.sequence = i
        
        sw.workout_name = exercise[i]
        sw.set = set[i]
        sw.count = cnt[i]
        sw.breaktime = 0

        crud.save_counted_workout(db, sw)
    
    return "saved!"
    
@app.post("/workout_data")
async def recent_workouts(db: Session = Depends(get_db)):

    most_recents = crud.get_recent_sessions(db)
    return_list = []

    for session in most_recents:

       workout_flow = crud.get_workout_flows_by_id(db, session.id)
       workout_flow.insert(0, session.date_time)
       return_list.append(workout_flow)

    return return_list
@app.post("/offer2")
async def offer(params: Live):
    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "workout_start.wav"))
    recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        if track.kind == "audio":
            local_audio = AudioTransformTrack(track)
        elif track.kind == "video":
            global local_video

            local_video = VideoTransformTrack2(track)
            pc.addTrack(local_video)
            recorder.addTrack(track)

        @track.on("ended")
        async def on_ended():
            await recorder.stop()
            await pc.close()
    @pc.on("datachannel")
    def on_datachannel(channel):
        global local_video
        local_video.channel=channel
        @channel.on("message")
        def on_message(message):
            channel.send("msg")
    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    
async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    uvicorn.run("server:app",
                host="0.0.0.0",
                port=8080,
                ssl_keyfile="./localhost+2-key.pem",
                ssl_certfile="./localhost+2.pem",
                reload=True)
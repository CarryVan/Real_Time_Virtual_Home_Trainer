import asyncio
import logging
import os
import uuid
import time
import pickle

import cv2
import pose_module as pm
# from aiohttp import web
from av import VideoFrame
import uvicorn

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from VideoTransformTrack import VideoTransformTrack, AudioTransformTrack
from src.schemas import Offer
ROOT = os.path.dirname(__file__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
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

@app.get("/start.html", response_class=HTMLResponse)
async def start(request: Request):
    content = open(os.path.join(ROOT, f"templates/start.html"),
                   "r", encoding='UTF8').read()
    return templates.TemplateResponse("start.html", {"request": request})

@app.post("/offer")
async def offer(params: Offer):
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
            # pc.addTrack(local_audio) 
            # recorder.addTrack(track)   
        elif track.kind == "video":
            local_video = VideoTransformTrack(
                track, exercise_list=params.exercise, cnt_list=params.cnt, set_list=params.set, breaktime_list=params.breaktime
            )
            pc.addTrack(local_video)

        @track.on("ended")
        async def on_ended():
            await recorder.stop()
            await pc.close()

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
                port=8081,
                ssl_keyfile="./localhost+2-key.pem",
                ssl_certfile="./localhost+2.pem",
                reload=True)
import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import time

import cv2
from starlette.responses import RedirectResponse
import pose_module as pm
# from aiohttp import web
from av import VideoFrame
import numpy as np
import uvicorn 

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.schemas import Offer

ROOT = os.path.dirname(__file__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger("pc")
pcs = set()

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    kind = "video"
    def __init__(self, track, exercise_list, cnt_list, set_list, breaktime_list):
        super().__init__()  # don't forget this!
        self.track = track
        self.detector = pm.poseDetector(model_dir='./model/all_model/body_language_lr.pkl')
        self.pTime = 0
        self.cnt = 0
        self.drop = -1
        self.exercise_list = exercise_list
        self.cnt_list = cnt_list
        self.set_list = set_list
        self.breaktime_list = breaktime_list
        
    async def recv(self):
        self.drop += 1
        frame = await self.track.recv()
        if self.drop % 2 == 0:
            self.drop = 0
            #pose estimate
            img = frame.to_ndarray(format="bgr24")
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            img = cv2.flip(img, 0)
            img, blc, blp, cnt = self.detector.draw_count(img, cnt=self.cnt, draw=True)
            self.cnt = cnt
            # rebuild a VideoFrame, preserving timing information
            cv2.putText(img, blc, (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)    
            cv2.putText(img, blp, (250, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 
            cv2.putText(img, 'cnt: ' + str(cnt), (30, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            self.before_frame = new_frame
            return new_frame
        else:
            return self.before_frame
        

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
    content = open(os.path.join(ROOT, f"templates/record.html"), "r", encoding='UTF8').read()
    return templates.TemplateResponse("record.html", {"request": request})

@app.get("/start.html", response_class=HTMLResponse)
async def start(request: Request):
    content = open(os.path.join(ROOT, f"templates/start.html"), "r", encoding='UTF8').read()
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
            pc.addTrack(player.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            local_video = VideoTransformTrack(
                track, exercise_list=params.exercise, cnt_list=params.cnt, set_list=params.set, breaktime_list=params.breaktime
            )
            # if end:
            #     RedirectResponse(url='/record.html')
            pc.addTrack(local_video)

        @track.on("ended")
        async def on_ended():
            await recorder.stop()

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
                reload=True)

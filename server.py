import asyncio
import logging
import os
import uuid
import time
import pickle
import sys
from datetime import datetime

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
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger("pc")
pcs = set()
class AudioTransformTrack(MediaStreamTrack):
    
    kind = "audio"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track

    async def recv(self):
        audio = await self.track.recv()
        # player = MediaPlayer(os.path.join(ROOT, "workout_start.wav"))
        # audio = player.audio
        return audio

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    kind = "video"
    def __init__(self, track, exercise_list, cnt_list, set_list, breaktime_list):
        super().__init__()  # don't forget this!
        self.track = track
        self.detector = pm.poseDetector(
            model_dir='./model/all_model/body_language_lr.pkl')
        self.pTime = 0
        self.cnt = 0
        self.drop = -1
        self.set_list = list(map(int,set_list.split(",")))
        self.pre_set=1
        if breaktime_list != '':
            self.breaktime_list = list(map(int, breaktime_list.split(",")))
        else:
            self.breaktime_list=[]
        self.breaktime_list.append(10)
        self.cnt_list = cnt_list.split(",")
        self.exercise_list = exercise_list.split(",")
        self.start_time = time.time()
        self.break_time = time.time()
        self.next_time = time.time()
        self.finish_time = time.time()
        self.goodjob_time = time.time()
        self.plank_time = "None"

        self.posture = "None"
        self.preposture = "None"

        self.goal = list(map(int, self.cnt_list))
        self.flow = -1
        # self.model="None"
        with open(f'./model/{str(self.exercise_list[0])}_model/body_language_lr.pkl', 'rb') as f:
            self.model = pickle.load(f)
        self.status = "None"
        self.i = 0
        self.idxx = 10
        self.sports = ""
        self.SPORTS = ""
        self.time = 3

        self.label_d=""
        self.label_u=""

    async def recv(self):
        self.drop += 1
        frame = await self.track.recv()
        if self.drop % 3 == 0:
            self.drop = 0
            # pose estimate
            img = frame.to_ndarray(format="bgr24")
            #=================for webcam ==========================
            # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE) 
            #img = cv2.flip(img, 0)
        
            if self.i < len(self.exercise_list):
                if self.flow == -1:
                    self.start_time = time.time()
                    self.sports = self.exercise_list[self.i]
                    self.label_d = f'{self.sports}_d'
                    self.label_u = f'{self.sports}_u'
                    self.preposture = self.label_u
                    self.SPORTS = self.sports.upper()
                    if self.sports == 'plank':
                        self.idxx = 11
                        self.label_d = f'{self.sports}_x'
                    elif self.sports == 'pushup':
                        self.SPORTS = "PUSH-UP"
                    elif self.sports == 'squat' or self.sports =='lunge':
                        self.preposture = self.label_d
                    elif self.sports =="legraise":
                        temp=self.label_d
                        self.label_d=self.label_u
                        self.label_u=temp
                    self.flow = 0

                if self.flow == 0 and time.time()-self.start_time < self.time:
                    img = self.detector.title(
                        img, self.SPORTS, str(self.cnt_list[self.i]))
                elif self.flow == 0 and time.time()-self.start_time >= self.time:
                    self.flow = 1
                
                if self.flow == 1 and self.posture != self.preposture:
                    img, self.posture = self.detector.set_posture(
                        img, self.idxx, self.model, "None",self.preposture, f'./dataset/example/{self.sports}.JPG', 200)
                elif self.flow == 1 and self.posture == self.preposture:
                    self.flow = 2
                
                
                if self.flow == 2 and self.cnt < self.goal[self.i]:
                    if self.idxx == 11:
                        img, self.status, self.cnt, self.plank_time = self.detector.exercise(
                            img, self.idxx, self.model, self.status, self.label_d, self.label_u, self.preposture, self.cnt, self.goal[self.i], self.plank_time)
                    else:
                        img, self.status, self.cnt = self.detector.exercise(
                            img, self.idxx, self.model, self.status, self.label_d, self.label_u, self.preposture, self.cnt, self.goal[self.i])
                        self.finish_time = time.time()
                elif self.flow == 2 and self.cnt >= self.goal[self.i]:
                    self.flow = 3
                

                if self.flow == 3 and time.time()-self.finish_time < 0.8:
                    img = self.detector.complete_sports(
                        img, self.cnt, self.goal[self.i])
                    self.break_time = time.time()
                elif self.flow == 3 and time.time() - self.finish_time >= 0.8:
                    
                    if self.i == len(self.exercise_list)-1 and self.pre_set==self.set_list[self.i]:
                        self.flow = 6
                        self.goodjob_time = time.time()
                    else:
                        self.flow = 4
                        self.breaktime = self.breaktime_list[self.i]
                    
                    
                if self.flow == 4 and time.time()-self.break_time < self.breaktime:
                    img = self.detector.title(img, "BREAK TIME", str(
                        self.breaktime-int(time.time()-self.break_time)))
                    self.next_time = time.time()

                elif self.flow == 4 and time.time()-self.break_time >= self.breaktime:
                    self.flow = 5

                if self.flow == 5 and time.time()-self.next_time < self.time:
                    if self.pre_set==self.set_list[self.i]:
                        img = self.detector.title(
                            img, "FINISH", "next "+f"{self.exercise_list[self.i+1]}".upper())
                    else:
                        img= self.detector.title(
                            img, "FINISH", "next SET "+ str(self.pre_set+1))
                elif self.flow == 5 and time.time()-self.next_time >= self.time:
                    if self.pre_set==self.set_list[self.i]:
                        self.i += 1
                        self.preposture = f'{str(self.exercise_list[self.i])}_u'
                        with open(f'./model/{str(self.exercise_list[self.i])}_model/body_language_lr.pkl', 'rb') as f:
                            self.model = pickle.load(f)
                        self.pre_set=1
                        self.idxx=10
                    else:
                        self.pre_set+=1
                    self.flow = -1
                    self.posture = "None"
                    self.cnt = 0
                if self.flow == 6:
                    img = self.detector.title(img, "EXCELLENT", "내일 또 만나요",100,50,6,7)
                        
                # if self.flow == 6 and time.time()-self.goodjob_time < self.time+8:
                #     img = self.detector.title(img, "Excellent", "내일 또 만나요",105,50,6,7)

                # elif self.flow == 6 and time.time()-self.goodjob_time >= self.time:
                #     pass

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
            # await pc.close()
            coros = [pc.close() for pc in pcs]
            await asyncio.gather(*coros)
            pcs.clear()


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

    print(f"params: {params}")
    for i in range(tot_len):
        index = i//2
        sw = SaveWorkout
        sw.workout_session = int(most_recent.id) + 1
        sw.sequence = i
        
        if i%2 == 0:    
            sw.workout_name = exercise[index]
            sw.set = set[index]
            sw.count = cnt[index]
            sw.breaktime = 0

        else:
            sw.workout_name = "break"
            sw.set = 0
            sw.count = 0
            sw.breaktime = breaktime[index]
            
        crud.save_counted_workout(db, sw)
    
    return "saved!"
    
@app.post("/recent_workout", response_model=List[schemas.WorkoutFlow])
async def recent_workout(db: Session = Depends(get_db)):

    most_recent = crud.get_recent_session(db)
    print(most_recent)

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    uvicorn.run("server:app",
                host="0.0.0.0",
                port=8080,
<<<<<<< HEAD
                reload=True)
=======
                ssl_keyfile="./localhost+2-key.pem",
                ssl_certfile="./localhost+2.pem",
                reload=True)
>>>>>>> 0b71ded141fefd12235caac035ed80f98c4aba6b

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
import pose_module as pm
import time
import pickle
import cv2
from av import VideoFrame
from tensorflow.keras import models
import os
import tensorflow as tf
import numpy as np
import copy
import time
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
            model_dir='./model/all_model/body_language_mlp.pkl')
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
        with open(f'./model/{str(self.exercise_list[0])}_model/body_language_mlp.pkl', 'rb') as f:
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
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            img = cv2.flip(img, 0)
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
                        with open(f'./model/{str(self.exercise_list[self.i])}_model/body_language_mlp.pkl', 'rb') as f:
                            self.model = pickle.load(f)
                        self.pre_set=1
                        self.idxx=10
                    else:
                        self.pre_set+=1
                    self.flow = -1
                    self.posture = "None"
                    self.cnt = 0
                        
                if self.flow == 6 and time.time()-self.goodjob_time < self.time:
                    img = self.detector.title(img, "참 잘했어요", "bb")

                elif self.flow == 6 and time.time()-self.goodjob_time >= self.time:
                    pass
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            self.before_frame = new_frame
            return new_frame
        else:
            return self.before_frame

class VideoTransformTrack2(MediaStreamTrack):
    
    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.model = models.load_model(f'./model/all_model')
        self.class_number = {3: 'lunge_d', 2: 'lunge_u', 4: 'squat_d', 5: 'squat_u', 8: 'legraise_u', 9: 'legraise_d', 11: 'plank_u', 13: 'sitting_d',
                           15: 'walking_u', 16: 'pushup_u', 17: 'pushup_d', 0: 'none_u'}
        self.detector = pm.poseDetector(
            model_dir='./model/all_model/body_language_mlp.pkl')
        self.sequence = []
        self.before_status = "walking_u"
        self.drop = -1
        # self.before_frame = ""
        self.pose_predict = 0
        self.pose_prob = 0
        self.plank_cnt = 0
        self.plank_start_time = 0
        self.workout_cnt = {'lunge': 0, 'squat': 0, 'legraise': 0, 'plank': 0, 'pushup': 0}

    async def recv(self):
        try:
            self.drop += 1
            frame = await self.track.recv()
            img = frame.to_ndarray(format="bgr24")
            # tmp_img = cv2.resize(img, (480,640))
            
            img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            img = cv2.flip(img, 0)
            
            if self.drop % 4 == 0:
                
                pose_row = self.detector.all_classify(img)
                self.sequence.append(np.array(pose_row))
                if len(self.sequence) == 3:
                    res = self.model.predict(np.expand_dims(self.sequence, axis=0))[0]
                    self.sequence = self.sequence[1:]
                    self.pose_predict = np.argmax(res)
                    self.pose_prob = res[np.argmax(res)]

                self.status = self.class_number[self.pose_predict].split("_")
                
                if self.status[0] != "plank" and self.status[0] == self.before_status[0] and self.before_status[1] == "d" and self.status[1] == "u":
                    self.workout_cnt[self.status[0]] += 1
                
                if self.status[0] != 'plank':
                    self.plank_start_time = 0
                
                elif self.status[0] == "plank":
                    if not self.plank_start_time:
                        self.plank_start_time = time.time()
                    self.plank_time = time.time()
                    if int(self.plank_time - self.plank_start_time) >= 1:
                        self.workout_cnt[self.status[0]] += int(self.plank_time - self.plank_start_time)
                        self.plank_start_time = self.plank_time
                self.before_status = self.status
                
            cv2.putText(img, self.class_number[self.pose_predict], (30, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)    
            cv2.putText(img, str(round(self.pose_prob, 2)), (330, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 

            cv2.putText(img, 'pushup' + str(self.workout_cnt['pushup']), (30, 270), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 
            cv2.putText(img, 'lunge' + str(self.workout_cnt['lunge']), (30, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 
            cv2.putText(img, 'plank' + str(self.workout_cnt['plank']), (30, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 
            cv2.putText(img, 'squat' + str(self.workout_cnt['squat']), (30, 190), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 
            cv2.putText(img, 'legraise' + str(self.workout_cnt['legraise']), (30, 230), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 

            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            self.before_frame = new_frame
            return new_frame
            
        except Exception as e:
            print(e) 
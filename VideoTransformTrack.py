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
import json

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    kind = "video"
    def __init__(self,track, exercise_list, cnt_list, set_list, breaktime_list):
        super().__init__()  # don't forget this!
        self.track = track
        self.detector = pm.poseDetector()
        self.cnt = 0
        self.drop = -1
        self.set_list = list(map(int,set_list.split(",")))
        self.pre_set=1
        self.total_set=1
        if len(breaktime_list)!=0:
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
        self.channel=None
        self.progress={}
        self.progress['exercise']=self.exercise_list
        self.progress['cnt']=self.goal
        self.progress['set']=[0]*len(self.cnt_list)
        self.progress['exit']=1
    async def recv(self):
        self.drop += 1
        frame = await self.track.recv()
        if self.drop % 3 == 0:
            self.drop = 0
            # pose estimate
            img = frame.to_ndarray(format="bgr24")
            # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            img = cv2.flip(img, 1)
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
                    self.progress['set'][self.i]=self.pre_set
                    if self.channel is not None:
                        self.channel.send(
                            json.dumps(self.progress)
                        )
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
                        self.total_set=1
                        self.idxx=10
                    else:
                        self.pre_set+=1
                        self.total_set+=1
                    self.flow = -1
                    self.posture = "None"
                    self.cnt = 0
                ##현재 정해진 운동 완료하면 자동으로 record로 가는데, 계속 띄워놓고 싶으면 이걸로
                # if self.flow == 6:
                    # img = self.detector.title(img, "EXCELLENT", "내일 또 만나요",105,50,6,7)
                        
                if self.flow == 6 and time.time()-self.goodjob_time < self.time:
                    img = self.detector.title(img, "Excellent", "내일 또 만나요",105,50,6,7)

                elif self.flow == 6 and time.time()-self.goodjob_time >= self.time:
                    self.progress['finish']=1
                    if self.channel is not None:
                        self.channel.send(
                            json.dumps(self.progress)
                        )

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
        try:
            # self.model = models.load_model('./model/all4_model')

            self.model = tf.lite.Interpreter(model_path="./model/all7_model.tflite")
            self.model.allocate_tensors()
            self.input_details = self.model.get_input_details()
            self.output_details = self.model.get_output_details()
        except Exception as e:
            print(e)
        self.class_number ={8: 'legraise_u', 9: 'legraise_d', 20: 'lunge_d', 21: 'lunge_u', 27: 'plank_u', 36: 'pushup_d', 37: 'pushup_u', 59: 'sitting_u', 42: 'situp_u', 43: 'situp_d', 52: 'squat_d', 53: 'squat_u', 61: 'walking_u', 0: 'none_u'}
                           
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
        self.workout_cnt = {'lunge': 0, 'squat': 0, 'legraise': 0, 'plank': 0, 'pushup': 0, 'situp' : 0, 'dumbbell' : 0}
        self.workout = {'lunge': -40, 'squat': -40, 'legraise': -40, 'plank': -40, 'pushup': -40, 'situp' : -40, 'dumbbell' : -40}
        self.key  = ['lunge', 'squat', 'legraise', 'plank', 'pushup', 'situp', 'dumbbell']
        self.cnt = 0
        self.channel=None
        
    async def recv(self):
        try:
            
            self.drop += 1
            frame = await self.track.recv()
            img = frame.to_ndarray(format="bgr24")
            
            # img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            # img = cv2.flip(img, 0)
            if self.drop % 4 == 0:
                self.drop = 0
                pose_row = self.detector.all_classify(img)
                self.sequence.append(np.array(pose_row))
                if len(self.sequence) == 3:
                    input_data = np.expand_dims(self.sequence, axis=0)
                    input_data = np.array(input_data, dtype=np.float32)
                    self.model.set_tensor(self.input_details[0]['index'], input_data)
                    self.model.invoke()
                    res = self.model.get_tensor(self.output_details[0]['index'])[0]
                    
                
                    # res = self.model.predict(np.expand_dims(self.sequence, axis=0))[0]
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
                try:
                    if self.channel is not None :
                        self.channel.send(
                            json.dumps(self.workout_cnt)
                        )
                except Exception as e:
                    print(e)
            
            
            for i in self.key:
                if self.workout_cnt[i] != 0:
                    self.cnt += 30
                    self.workout[i] = self.cnt
                    self.key.remove(i)

              
                    

            cv2.putText(img, 'pushup' + str(self.workout_cnt['pushup']), (30, self.workout['pushup']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 
            cv2.putText(img, 'lunge' + str(self.workout_cnt['lunge']), (30, self.workout['lunge']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 
            cv2.putText(img, 'plank' + str(self.workout_cnt['plank']), (30, self.workout['plank']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 
            cv2.putText(img, 'squat' + str(self.workout_cnt['squat']), (30, self.workout['squat']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 
            cv2.putText(img, 'legraise' + str(self.workout_cnt['legraise']), (30, self.workout['legraise']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 
            cv2.putText(img, 'situp' + str(self.workout_cnt['situp']), (30, self.workout['situp']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 
            cv2.putText(img, 'dumbbell' + str(self.workout_cnt['dumbbell']), (30, self.workout['dumbbell']), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA) 


            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            # self.before_frame = new_frame
            return new_frame
        except Exception as e:
            
            print(e)
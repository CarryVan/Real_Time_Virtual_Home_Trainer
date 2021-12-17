from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
import pose_module as pm
import time
import pickle
import cv2
from av import VideoFrame


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
    global finish
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
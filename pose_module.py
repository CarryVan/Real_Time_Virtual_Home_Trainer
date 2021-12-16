import cv2
import mediapipe as mp

import numpy as np
import time
from PIL import ImageFont, ImageDraw, Image

class poseDetector:
 
    def __init__(self,
               static_image_mode=False,
               model_complexity=1,
               smooth_landmarks=True,
               enable_segmentation=False,
               smooth_segmentation=True,
               min_detection_confidence=0.5,
               min_tracking_confidence=0.5,
               model_dir=None):
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.smooth_landmarks = smooth_landmarks
        self.enable_segmentation = enable_segmentation
        self.smooth_segmentation = smooth_segmentation
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence= min_tracking_confidence
 
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.static_image_mode,
                                    self.model_complexity,
                                    self.smooth_landmarks,
                                    self.enable_segmentation,
                                    self.smooth_segmentation,
                                    self.min_detection_confidence,
                                    self.min_tracking_confidence)
        self.status = 'pushup_x'
        self.joint = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
        # with open(f'{model_dir}', 'rb') as f:
            # self.model = pickle.load(f)

    
    def drawTitle(self,img,title,size,y):
        
        width,height=img.size
        # height,width=img.size
        # print(height,width)
        # print(type(img))
        try: 
            draw = ImageDraw.Draw(img)
            font=ImageFont.truetype("font/GodoM.ttf",size)
            text=str(title)
            w,h=draw.textsize(text,font=font)
            
            if y==0:
                org=((width-w)//2,(height-h)//2-h)
            elif y==1:
                org=((width-w)//2,(height-h)//2+h)
            elif y==3:
                org=((width-w)//2,(height-h)//2-h*2.5)
            elif y==4:
                org=((width-w)//2,(height-h)//2-1.5*h)
            elif y==5:
                org=((width-w*2.5),(h))
            draw.text(org,text,font=font,fill=(255,255,255))
        except Exception as e:
            print(e)
        return img
    def title(self, img,title,plus):
        img.flags.writeable = True
        img = Image.fromarray(img)
        try:
            img = self.drawTitle(img,title,85,0)
            img=self.drawTitle(img, plus, 85, 1)
        except Exception as e:
            print(e)
        img = np.array(img)
        return img

    def set_posture(self,img,idxx,model,first,preposture,location,y,x=None):
        try:
            height, width, c = img.shape
            src=cv2.imread(location,cv2.IMREAD_UNCHANGED)
            sh0,sw0,c=src.shape
            ratio=sw0/sh0
            src=cv2.resize(src,(int(width//2+(width//8)*ratio),int(height//2+(1-ratio)*(height//8))))
            sh,sw,c=src.shape
            overlay_alpha=src[:,:,:3]/255.0
            background_alpha = 1.0 -overlay_alpha
            x=(width-sw)//2
            y=int(height-sh*1.1)
            img.flags.writeable = True
            empty_img=img
            results = self.pose.process(empty_img)
            img[y:y+sh,x:x+sw]=overlay_alpha*src[:,:,:3]+background_alpha*img[y:y+sh,x:x+sw]
            try:
                psland=results.pose_landmarks
                if psland!= None:
                    landmarks = psland.landmark
                joint_cnt = [landmark.visibility for idx, landmark in enumerate(landmarks) if landmark.visibility > 0.5 and idx in self.joint]
                pose_row = list(np.array([[landmark.x, landmark.y, landmark.z] for idx, landmark in enumerate(landmarks) if idx in self.joint]).flatten())
                if len(joint_cnt) < 5:
                    raise Exception
                # X = pd.DataFrame([pose_row])
                first = model.predict([pose_row])[0]
            except Exception as e:
                print(e)
            
            img = Image.fromarray(empty_img)
            img=self.drawTitle(img, "준비 자세를", 45, 3)
            img=self.drawTitle(img, "취해주세요" , 45, 4)
        except Exception as e:
            print(e)

        img = np.array(img)
        return img,first
    def exercise(self,img,idxx,model,status,label_d,label_u,preposture,cnt,goal,start_time=None):
        img.flags.writeable = True
        height,width,c=img.shape
        prog=int(width*0.9)

        margin=int(width*0.1)
        pad=int(height*0.85)
        empty_img=img
        results = self.pose.process(empty_img)
        self.mpDraw.draw_landmarks(empty_img, results.pose_landmarks,
                                           self.mpPose.POSE_CONNECTIONS)
        try:
            # Extract Pose landmarks
            
            landmarks = results.pose_landmarks.landmark
            joint_cnt = [landmark.visibility for idx, landmark in enumerate(landmarks) if landmark.visibility > 0.5 and idx in self.joint]
            pose_row = list(np.array([[landmark.x, landmark.y, landmark.z] for idx, landmark in enumerate(landmarks) if idx in self.joint]).flatten())
                
            # X = pd.DataFrame([pose_row])
            body_language_class = model.predict([pose_row])[0]
            if idxx==11:
                if status == label_d and body_language_class == label_u:
                    start_time =time.time()
                elif status == label_u and body_language_class == label_u:
                    end_time = time.time()
                    if start_time=="None":
                        start_time=end_time

                    total_time = end_time - start_time
                    if int(total_time) >=1:
                        cnt += 1
                        start_time = time.time()
            else:
                if status == label_d and body_language_class == label_u:
                    cnt +=1
            status = body_language_class
            #우리 확인용
            cv2.putText(empty_img, body_language_class, (30, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)    
            
            img = Image.fromarray(empty_img)
            self.drawTitle(img, str(cnt) , 65, 5)
            img = np.array(img)
            
            cv2.line(img,(margin+((prog-margin)//goal)*cnt,pad),(prog,pad),(220,220,220),7)
            cv2.line(img,(margin,pad),(margin+((prog-margin)//goal)*cnt,pad),(0,225,0),7)
            if idxx==11:
                return img, status, cnt , start_time    
            else:
                return img, status, cnt 
            
        except Exception as e:
            print(e)
            try:
                img = Image.fromarray(empty_img)
                self.drawTitle(img, str(cnt) , 65, 5)
                img = np.array(img)
                cv2.line(img,(margin+((prog-margin)//goal)*cnt,pad),(prog,pad),(220,220,220),7)
                cv2.line(img,(margin,pad),(margin+((prog-margin)//goal)*cnt,pad),(0,225,0),7)
            except Exception as e:
                print(e)
            if idxx==11:
                return img, status, cnt , start_time    
            else:
                return img, status, cnt 
    def complete_sports(self,img,cnt,goal):
        img.flags.writeable = True
        height,width,c=img.shape
        try:
            img = Image.fromarray(img)
            self.drawTitle(img, str(cnt) , 65, 5)
            img = np.array(img)
        except Exception as e:
            print(e)
        prog=int(width*0.9)

        margin=int(width*0.1)
        pad=int(height*0.85)
        cv2.line(img,(margin,pad),(margin+((prog-margin)//goal)*cnt,pad),(0,225,0),7)
        return img
   


 

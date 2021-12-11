import cv2
import mediapipe as mp

import numpy as np
import pickle
import time

class poseDetector():
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
        with open(f'{model_dir}', 'rb') as f:
            self.model = pickle.load(f)

    def draw_count(self, img, draw, cnt):
        # empty_img = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                           self.mpPose.POSE_CONNECTIONS)

        try:
            landmarks = self.results.pose_landmarks.landmark
            joint_cnt = [landmark.visibility for idx, landmark in enumerate(landmarks) if landmark.visibility > 0.5 and idx in self.joint]
            pose_row = list(np.array([[landmark.x, landmark.y, landmark.z] for idx, landmark in enumerate(landmarks) if idx in self.joint]).flatten())
            if len(joint_cnt) < 5:
                raise Exception
            body_language_class = self.model.predict([pose_row])[0]
            body_language_prob = self.model.predict_proba([pose_row])[0]
            body_language_prob = str(round(body_language_prob[np.argmax(body_language_prob)],2))
            if self.status == 'pushup_d' and body_language_class == 'pushup_u':
                cnt += 1
            self.status = body_language_class
      
        except:
            body_language_class = "None"
            body_language_prob = "None"
       
        
        return img, body_language_class, body_language_prob, cnt


 

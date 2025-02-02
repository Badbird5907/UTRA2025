import cv2
import logging
from npsocket import SocketNumpyArray
import numpy as np
import cv2
import numpy as np
from openvino import Core
import math
from PID_controller import PIDController
from globals import *
from ws_motor_controller import DifferentialDriveController
import redis
import json  # Add this import

import pyrealsense2 as rs
import numpy
from io import BytesIO
from npsocket import SocketNumpyArray
import socket
from globals import *

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, resolution_x, resolution_y, rs.format.z16, 60)
config.enable_stream(rs.stream.color, resolution_x, resolution_y, rs.format.bgr8, 60)
pipeline.start(config)

hole_filling = rs.hole_filling_filter(2)
temporal = rs.temporal_filter()
spatial = rs.spatial_filter()


colorizer = rs.colorizer()

# align depth and color frames
align_to = rs.stream.color
align = rs.align(align_to)



# Initialize models
core = Core()
# Face detection model
face_detector = core.read_model("intel/face-detection-retail-0004/FP32/face-detection-retail-0004.xml")
compiled_face_detector = core.compile_model(face_detector, "CPU")
face_output_layer = compiled_face_detector.output(0)

# Age-Gender recognition model
age_gender_model = core.read_model("intel/age-gender-recognition-retail-0013/FP32/age-gender-recognition-retail-0013.xml")
compiled_age_gender = core.compile_model(age_gender_model, "CPU")
# Get only the two outputs: [age, gender]
age_output = compiled_age_gender.output("age_conv3")  # or output(0)
gender_output = compiled_age_gender.output("prob")    # or output(1)

# Emotion recognition model
emotion_model = core.read_model("intel/emotions-recognition-retail-0003/FP32/emotions-recognition-retail-0003.xml")
compiled_emotion = core.compile_model(emotion_model, "CPU")
emotion_output_layer = compiled_emotion.output(0)

# Labels for emotions
emotions = ['neutral', 'happy', 'sad', 'surprise', 'anger']

show_crops = True

PID_theta = PIDController(kp=1)
PID_distance = PIDController(kp=1)

drivebase = DifferentialDriveController(robot_ip, robot_port, 255)

# Initialize Redis client
redis_client = redis.Redis(
        host='192.168.137.1',
        port=6379,
        password=None,
        decode_responses=True)

def redis_publish(data):
    if not data:
        return
    
    # Get the first face data (closest person)
    face = data[0]
    face['distance_mm'] = int(face['distance_mm'])  # Ensure distance is serializable
    
    # Convert face data to JSON string
    face_json = json.dumps(face)
    
    # Store in Redis with key 'face_data'
    redis_client.set('face_data', face_json)

def trigger_ai():
    # Trigger AI processing
    redis_client.publish('ai_trigger', 'this is how im feeling')


def crop_face(frame, detection, distance, k_padding=0):
    padding = int(k_padding * distance)
    xmin = max(int(detection[3] * frame.shape[1]) - padding, 0)
    ymin = max(int(detection[4] * frame.shape[0]) - padding, 0)
    xmax = min(int(detection[5] * frame.shape[1]) + padding, frame.shape[1])
    ymax = min(int(detection[6] * frame.shape[0]) + padding, frame.shape[0])
    if show_crops:
        cv2.imshow(f"Face Crop", frame[ymin:ymax, xmin:xmax])
    return frame[ymin:ymax, xmin:xmax]

def process_frame(frame, depth_map):
    # Prepare input for face detection
    input_image = cv2.resize(frame, (300, 300))
    input_image = input_image.transpose((2, 0, 1))
    input_image = np.expand_dims(input_image, 0)
    
    # Run face detection
    results = compiled_face_detector([input_image])[face_output_layer]
    detections = results[0][0]

    face_data = []
    
    # Process detections
    for detection in detections:
        confidence = float(detection[2])
        if confidence > 0.5:  # Confidence threshold
            xmin = int(detection[3] * frame.shape[1])
            ymin = int(detection[4] * frame.shape[0])
            xmax = int(detection[5] * frame.shape[1])
            ymax = int(detection[6] * frame.shape[0])

            # Get depth for face center
            face_center_x = (xmin + xmax) // 2
            face_center_y = (ymin + ymax) // 2

            distance = depth_map[face_center_y, face_center_x]
            
            # Crop and process face
            face = crop_face(frame, detection, distance)
            if face.size == 0:
                distance = 0

                
            # Process age-gender
            face_input = cv2.resize(face, (62, 62))
            face_input = face_input.transpose((2, 0, 1))
            face_input = np.expand_dims(face_input, 0)
            
            # Get age and gender predictions separately
            results = compiled_age_gender([face_input])
            age = results[age_output][0][0][0][0] * 100
            gender_prob = results[gender_output][0][1]
            gender = "Male" if gender_prob > 0.5 else "Female"
            
            # Process emotion
            emotion_input = cv2.resize(face, (64, 64))
            emotion_input = emotion_input.transpose((2, 0, 1))
            emotion_input = np.expand_dims(emotion_input, 0)
            
            emotion = compiled_emotion([emotion_input])[emotion_output_layer]
            emotion_label = emotions[np.argmax(emotion)]
            
            # Draw detection box
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)

            # Draw information
            info_text = f"Age: {int(age)}  {emotion_label}"
            gender_text = f"{gender}: {float(gender_prob[0][0]):.2f}"
            dist_text = f"Distance: {distance}mm"
            cv2.putText(frame, info_text, (xmin, ymax + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, gender_text, (xmin, ymax + 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, dist_text, (xmin, ymax + 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
            face_data.append({
                'distance_mm': distance,
                'age_years': int(age),
                'gender': {
                    'label': gender,
                    'confidence': float(gender_prob[0][0])
                },
                'emotion': emotion_label,
                'bbox': {
                    'xmin': xmin,
                    'ymin': ymin,
                    'xmax': xmax,
                    'ymax': ymax
                },
                'center': {
                    'x': face_center_x,
                    'y': face_center_y
                },
                'size': (xmax - xmin, ymax - ymin)
            })

    face_data = sorted(face_data, key=lambda x: x['distance_mm'])
    
    return frame, face_data

def move_robot(face_data):
    if not face_data:
        return
    face_data = face_data[0]
    face_center = face_data['center']
    face_size = face_data['size']
    face_distance = face_data['distance_mm']

    theta = PID_theta.compute(resolution_x/2, face_center['x'], 1)
    distance = PID_distance.compute(400, face_distance, 1)

    left_speed = -distance - theta
    right_speed = -distance + theta

    print(f"Left: {left_speed}, Right: {right_speed}")
    # Move the drivebase it is a async function
    drivebase.move(left_speed, right_speed)



    

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    while True:
        # color_frame = color_socket.receive_array()
        # depth_map = depth_socket.receive_array()

        frames = pipeline.wait_for_frames()
        frames = align.process(frames)
        
        depth_frame = frames.get_depth_frame()
        depth_frame = hole_filling.process(depth_frame)
        depth_frame = temporal.process(depth_frame)
        depth_frame = spatial.process(depth_frame).as_depth_frame()
        if not depth_frame:
            continue
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = numpy.asanyarray(color_frame.get_data())
        depth_map = numpy.asanyarray(depth_frame.get_data())



        color_image, face_data = process_frame(color_image, depth_map)
        redis_publish(face_data)  # Add this line after process_frame

        if color_image is not None:
            cv2.imshow("Color Frame", color_image)
        
        # Press Q on keyboard to exit
        if cv2.waitKey(25) & 0xFF == ord("q"):
            break

        move_robot(face_data)

except KeyboardInterrupt:
    logger.info("Shutting down...")

finally:
    cv2.destroyAllWindows()



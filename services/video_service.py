from typing import List, Dict, Tuple, TypedDict, Generator
from collections import defaultdict
import cv2
import os

class Interval(TypedDict):
    start: float
    end: float

class Detection(TypedDict):
    class_name: str
    time: float

# YOLO
def detect_objects(frame, yolo_model) -> List[str]:
    results = yolo_model(frame)

    detected_classes: List[str] = []

    for *xyxy, conf, cls in results.xyxy[0]:
        class_name = yolo_model.names[int(cls)]
        detected_classes.append(class_name)
    
    return detected_classes, results.render()[0]

# 인터벌 계산
def calculate_intervals(detections_per_frame: List[List[str]], frame_rate: float) -> Dict[str, List[List[float]]]:
    class_intervals = defaultdict(list)
    previous_detections = defaultdict(lambda: {'time': 0, 'last_seen': -1})

    for frame_id, detected_classes in enumerate(detections_per_frame):
        time_stamp = frame_id / frame_rate

        for class_name in detected_classes:

            if class_name in previous_detections:
                prev_frame = previous_detections[class_name]

                if frame_id - prev_frame <= int(0.1 * frame_rate):
                    class_intervals[class_name][-1][1] = time_stamp
                else:
                    class_intervals[class_name].append([time_stamp, time_stamp])
            else:
                class_intervals[class_name].append([time_stamp, time_stamp])

            previous_detections[class_name] = frame_id

    return class_intervals
    
# 병합
def merge_intervals(intervals: List[List[float]], threshold: float = 0.7) -> List[List[float]]:
    merged: List[List[float]] = []

    for start, end in sorted(intervals, key=lambda x: x[0]):

        if merged and start - merged[-1][1] <= threshold:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return merged

# 이미지 캡쳐
def capture_frames(video_path: str, intervals: List[List[float]], class_name: str, upload_folder: str) -> Generator[Dict, None, None]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open the video file")

    for idx, interval in enumerate(intervals):
        mid_time = (interval[0] + interval[1]) / 2
        cap.set(cv2.CAP_PROP_POS_MSEC, mid_time * 1000)
        ret, frame = cap.read()
        if ret:
            #capture_filename = f"capture_{class_name}_{uuid.uuid4().hex}.jpg"
            capture_filename = f"capture_{class_name}_{idx}.jpg"
            capture_path = os.path.join(upload_folder, capture_filename)
            cv2.imwrite(capture_path, frame)  # 프레임 저장
            yield {
                'interval': interval,
                'capture_filename': capture_filename
            } 
    cap.release()

# 캡션 생성
def process_video(video_path: str, output_path: str, models: Dict, upload_folder: str) -> Dict:

    yolo_model = models["yolo"]

    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)

    detections_per_frame = []
    frames_rendered = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        detected_classes, rendered = detect_objects(frame, yolo_model)

        detections_per_frame.append(detected_classes)
        frames_rendered.append(rendered)

    cap.release()

    # interval 계산
    class_intervals = calculate_intervals(
        detections_per_frame,
        frame_rate
    )

    capture_images = {}

    for class_name, intervals in class_intervals.items():

        merged = merge_intervals(intervals)

        long_intervals = [
            i for i in merged if i[1] - i[0] >= 1
        ]

        captures = list(capture_frames(video_path, long_intervals, class_name, upload_folder)
        )

        capture_images[class_name] = captures

    return {
        "class_intervals": class_intervals,
        "capture_images": capture_images
    }

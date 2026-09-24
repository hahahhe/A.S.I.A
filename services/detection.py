from collections import defaultdict
import cv2
import torch
from flask import url_for, current_app
import os

from services.caption import generate_caption_for_image

device = 'cuda' if torch.cuda.is_available() else 'cpu'
other_device = 'cpu'
yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', path='oldfilm.pt').to(device)

print("yolo_model: ", device)

def merge_intervals(intervals, threshold=0.7):
    # 인터벌을 병합하는 함수 (threshold: 인접 인터벌 병합 임계값)
    merged = []
    for start, end in sorted(intervals, key=lambda x: x[0]):
        if merged and start - merged[-1][1] <= threshold:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def capture_at_intervals(video_path, intervals, class_name, upload_folder, ):
    # 비디오에서 특정 시간 간격의 이미지를 캡처
    cap = cv2.VideoCapture(video_path)
    capture_file_counts = defaultdict(int)
    if not cap.isOpened():
        raise ValueError("Could not open the video file")
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    for interval in intervals:
        mid_time = (interval[0] + interval[1]) / 2
        cap.set(cv2.CAP_PROP_POS_MSEC, mid_time * 1000)
        ret, frame = cap.read()
        if ret:
            #capture_filename = f"capture_{class_name}_{uuid.uuid4().hex}.jpg"
            capture_filename = f"capture_{class_name}_{capture_file_counts[class_name]}.jpg"            
            capture_path = os.path.join(upload_folder, capture_filename)
            cv2.imwrite(capture_path, frame)  # 프레임 저장
            caption = generate_caption_for_image(capture_path)
            yield {
                'time': mid_time,
                'interval': interval,
                'capture_url': url_for('video.uploaded_file', filename=capture_filename),
                'caption': caption,
                'capture_filename': capture_filename
            }
        capture_file_counts[class_name] += 1    
    cap.release()


def perform_detection_and_labeling(video_path, output_path):
    # 비디오에서 객체 탐지 및 라벨링 수행
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open the video file")
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # 'mp4v' 사용

    out = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))
    if not out.isOpened():
        raise ValueError("Could not open the video writer")

    class_intervals = defaultdict(list)
    previous_detections = defaultdict(lambda: {'time': 0, 'last_seen': -1})
    capture_images = defaultdict(list)

    frame_id = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = yolo_model(frame)
        frame_rendered = results.render()[0]
        out.write(frame_rendered)

        time_stamp = frame_id / frame_rate
        current_detections = defaultdict(lambda: {'time': 0, 'last_seen': -1})

        for *xyxy, conf, cls in results.xyxy[0]:
            class_name = yolo_model.names[int(cls)]
            current_detections[class_name]['time'] = time_stamp
            current_detections[class_name]['last_seen'] = frame_id

        for class_name, info in current_detections.items():
            if class_name in previous_detections and info['last_seen'] - previous_detections[class_name]['last_seen'] <= 0.1 * frame_rate:
                class_intervals[class_name][-1][1] = time_stamp
            else:
                class_intervals[class_name].append([time_stamp, time_stamp])

        previous_detections = current_detections
        frame_id += 1

    cap.release()
    out.release()

    # 캡처 이미지 및 캡션 생성 (1초 이상 지속되는 인터벌에 대해서만)
    for class_name, intervals in class_intervals.items():
        merged_intervals = merge_intervals(intervals)
        long_intervals = [interval for interval in merged_intervals if interval[1] - interval[0] >= 1]  # 1초 이상 지속되는 인터벌만 선택

        if long_intervals:
            captures = list(capture_at_intervals(video_path, long_intervals, class_name, current_app.config['UPLOAD_FOLDER']))
            capture_images[class_name].extend(captures)

        class_durations = []
        for class_name, intervals in class_intervals.items():
            merged_intervals = merge_intervals(intervals)
            long_intervals = [interval for interval in merged_intervals if interval[1] - interval[0] >= 1]

            if sum(e - s for s, e in long_intervals) >= 1:
                class_durations.append({
                    'class': class_name,
                    'intervals': long_intervals,
                    'total_duration': sum(e - s for s, e in long_intervals),
                    'captures': capture_images[class_name]
                })


    return class_durations, capture_images
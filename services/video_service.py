from typing import Dict
import cv2
from collections import defaultdict
import config
import os
from common.video_utils import generate_caption_for_image

# 영상 초기화
def init_video(video_path: str, output_path: str) -> Dict:
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
    
    return cap, out, frame_rate

# yolo 객체탐지
def detection_on_frame(frame, model):
    results = model(frame)
    frame_rendered = results.render()[0]

    return results, frame_rendered

def extra_current_detections(results, frame_id, time_stamp, model):
    current_detections = defaultdict(lambda: {'time': 0, 'last_seen': -1})

    for *xyxy, conf, cls in results.xyxy[0]:
        class_name = model.names[int(cls)]
        current_detections[class_name]['time'] = time_stamp
        current_detections[class_name]['last_seen'] = frame_id
    
    return current_detections


# 인터벌 계산
def update_intervals(class_intervals, previous_detections, current_detections, time_stamp, frame_rate):
    for class_name, info in current_detections.items():
            if class_name in previous_detections and info['last_seen'] - previous_detections[class_name]['last_seen'] <= 0.1 * frame_rate:
                class_intervals[class_name][-1][1] = time_stamp
            else:
                class_intervals[class_name].append([time_stamp, time_stamp])


# 병합
def process_video_frames(cap, model, out, frame_rate):
    class_intervals = defaultdict(list)
    previous_detections = defaultdict(lambda: {'time': 0, 'last_seen': -1})
    
    frame_id = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results, frame_rendered = detection_on_frame(frame, model)
        out.write(frame_rendered)

        time_stamp = frame_id / frame_rate
        current_detections = extra_current_detections(results, frame_id, time_stamp, model)
        
        update_intervals(class_intervals, previous_detections, current_detections, frame_rate, time_stamp)
        
        previous_detections = current_detections
        frame_id += 1
    
    return class_intervals

def merge_intervals(intervals, threshold=0.7):
    # 인터벌을 병합하는 함수 (threshold: 인접 인터벌 병합 임계값)
    merged = []
    for start, end in sorted(intervals, key=lambda x: x[0]):
        if merged and start - merged[-1][1] <= threshold:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

def capture_at_intervals(video_path, intervals, class_name, upload_folder, url_builder=None):
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

            if url_builder:
                capture_url = url_builder(capture_filename)
            else:
                capture_url = capture_path

            yield {
                'time': mid_time,
                'interval': interval,
                'capture_url': capture_url,
                'caption': caption,
                'capture_filename': capture_filename
            }
        capture_file_counts[class_name] += 1    
    cap.release()

def postprocess_intervals(class_intervals):
    processed = {}
    

    # 캡처 이미지 및 캡션 생성 (1초 이상 지속되는 인터벌에 대해서만)
    for class_name, intervals in class_intervals.items():
        merged = merge_intervals(intervals)
        long_intervals = [interval for interval in merged if interval[1] - interval[0] >= 1]  # 1초 이상 지속되는 인터벌만 선택

        if long_intervals:
            processed[class_name] = long_intervals

    return processed

def generate_captures(video_path, processed_intervals, class_name, upload_folder):
    capture_images = defaultdict(list)

    for class_name, intervals in processed_intervals:
        captures = list( capture_at_intervals(video_path, intervals, class_name, upload_folder))
        capture_images[class_name].extend(captures)
    
    return capture_images

def final_output(processed_intervals, capture_images):
    class_durations = []
    for class_name, intervals in processed_intervals.items():
        merged_intervals = merge_intervals(intervals)
        long_intervals = [interval for interval in merged_intervals if interval[1] - interval[0] >= 1]

        if sum(e - s for s, e in long_intervals) >= 1:
            class_durations.append({
                'class': class_name,
                'intervals': long_intervals,
                'total_duration': sum(e - s for s, e in long_intervals),
                'captures': capture_images[class_name]
            })
    return class_durations


def perform_detection_and_labeling(video_path, output_path, models):
    cap, out, frame_rate = init_video(video_path, output_path)
    yolo_model = models['yolo']

    class_intervals = process_video_frames(cap, out, frame_rate, yolo_model)

    cap.release()
    out.release()

    processed_intervals = postprocess_intervals(class_intervals)

    capture_images = generate_captures(
        video_path,
        processed_intervals,
        config.UPLOAD_FOLDER
    )

    class_durations = final_output(processed_intervals, capture_images)

    return class_durations, capture_images
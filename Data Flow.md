# Refactoring Log

## Informations
**Date:** 2026-09-20
**Author:** 최준혁
**Issue/Branch:** Data type / main

## Overview
Video -> Detection -> Interval -> Capture -> Caption -> Audio -> Final Video
해당 프로젝트는 위와 같이 데이터 형식이 계속 바뀌기 때문에 리팩토링 및 유지보수를 위해 데이터 형식을 문서화 한다.

## 파이프라인
UploadedVideo -> DetectionResult -> ClassIntervals -> CaptureInfo -> CaptionedCapture -> AudioClipInfo -> FinalVideo

## 데이터 흐름
POST /upload/video -> filename ->
POST /process/labels -> perform_detection_and_labeling() -> class_durations/capture_images ->
POST /process/audio -> capture_images -> audio_clips_info ->
POST /finalize/video -> labeled_video_path/audio_clips_info -> final.mp4

## 데이터 형식
POST /upload/video
rerutn
{
    "original_video_url": str,
    "filename": str
}
=> file_path: str

YOLO
return
results = yolo_model(frame)
Detection:
    class_name: str
    timestamp: float
    frame_id: int

class_intervals
return
class_intervals: dict[str, list[Interval]] 
Interval: 
    start: float 
    end: float
{
    "class1": [[start1, end1], [start2, end2]],
    "class2": [[start1, end1], [start2, end2]]
}

capture_images
{
    "car": [
        {
            "time": float
            "interval": [float, float]
            "capture_url": str(path),
            "caption": str,
            "capture_filename": str(file)
        }
    ]
}

audio_clips_info
AudioClipInfo:
    class_name: str
    path: str
    start_time: float
    duration: float
{
    'class': class_name,
    'path': sound_path,
    'start_time': capture['interval'][0],
    'duration': min(actual_duration, duration)
}



## Guideline

1. Upload

Input: Video File
Output: VideoInfo

filename
path
url

2. Detection

Input: VideoInfo.path
Output: Detection[]

class_name
timestamp
frame_id

3. Interval

Input: Detection[]
Output: ClassIntervals

class_name
start
end

4. Capture

Input: Video + Interval
Output: CaptureInfo[]

class_name
timestamp
interval
image_path

5. Caption

Input: CaptureInfo
Output: CaptionedCapture

CaptureInfo + caption

6. Audio

Input: caption + duration
Output: AudioClipInfo

path
start_time
duration
class_name

7. Compose

Input: Video + AudioClipInfo[]
Output: Final video


## Structure
A.S.I.A/
|
|-- app.py
|
|-- routes/
|   |-- video.py
|   |__ audio.py
|
|-- services/
|   |-- detection.py
|   |-- caption.py
|   |-- audio_generation.py
|   |__ video_composer.py
|
|-- models/
|   |__ schemas.py
|
|-- config.py
|
|-- uploads/
|-- saved_audios/
|__ effects/

app.py
- flask 생성
- config 등록
- blueprint 등록
- 서버 실행

models/
schemas.py
- Interval
- VideoInfo
- Detection
- CaptureInfo
- AudioClipInfo

services
detection.py
- frame 처리
- interval 생성
- merge_intervals
- capture

caption.py
- generate_caption_for_image()

audio_generation.py
- generate_sound_from caption()

video_composer.py
- add_audio_to_video()

routes/
video.py
- /upload/video
- /process/labels
- /finalize/video
- /uploads/<finename>

audio.py
- /process/audio
- /generate_audio
- /save_audio
- /getList
- /download
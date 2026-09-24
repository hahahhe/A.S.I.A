import math
import os
from moviepy import AudioFileClip, CompositeAudioClip, VideoFileClip, concatenate_audioclips
from flask import current_app

#from models.schemas import AudioClipInfo

def add_audio_to_video(video_path, audio_clips_info):
    # 비디오에 오디오 추가 - 수정된 버전
    print('add func: ', video_path, audio_clips_info)
    video_clip = VideoFileClip(video_path)
    audio_clips = []
    for clip_info in audio_clips_info:
        print('clip: ', clip_info)
        audio_clip = AudioFileClip(clip_info['path'])

        if audio_clip.duration > clip_info['duration']:
            audio_clip = audio_clip.subclipped(0, clip_info['duration'])

        audio_clip = audio_clip.with_start(clip_info['start_time'])
        audio_clips.append(audio_clip)

    composite_audio = CompositeAudioClip(audio_clips)
    video_clip_with_audio = video_clip.with_audio(composite_audio)

    output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"final.mp4")
    video_clip_with_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path

def merge_audio_files(audio_files: list[dict], video_file: str = "uploads/final.mp4", output_path: str = "static/uploads/merged_video.mp4"):
    # 오디오 파일 정보 출력
        for audio in audio_files:
            print(f"File: {audio['file']}, Start: {audio['start']}, End: {audio['end']}")
    
        # 비디오 파일 경로 정의
        video_file = 'uploads/final.mp4'
        video_clip = VideoFileClip(video_file)  # 비디오 클립 정의
    
        audio_clips = []  # 오디오 클립을 저장할 리스트
    
        for audio in audio_files:
            # 'List' 폴더와 'uploads' 폴더에서 오디오 파일 경로 찾기
            audio_path_list = [f"uploads/{audio['file']}", f"effects/{audio['file']}", f"saved_audios/{audio['file']}"]
            audio_path = next((path for path in audio_path_list if os.path.exists(path)), None)
    
            if audio_path is None:
                print(f"Audio file not found: {audio['file']}")
                continue
    
            original_audio_clip = AudioFileClip(audio_path)
            audio_duration = original_audio_clip.duration
    
            # 오디오 클립을 반복하여 적절한 길이로 만듭니다.
            repeat_count = math.ceil((audio['end'] - audio['start']) / audio_duration)
            repeated_audio_clip = concatenate_audioclips([original_audio_clip] * repeat_count)
    
            # 총 길이를 오디오 클립 길이로 조정합니다.
            audio_clip = repeated_audio_clip.subclipped(0, audio['end'] - audio['start'])
    
            # 오디오 클립을 비디오의 지정된 시간대에 배치
            audio_clip = audio_clip.with_start(audio['start'])
            audio_clips.append(audio_clip)
    
        # 모든 오디오 클립을 하나의 클립으로 합성
        final_audio = CompositeAudioClip(audio_clips)
    
        # 비디오에 오디오 추가
        final_clip = video_clip.with_audio(final_audio)
    
        # 결과 저장
        output_path = 'static/uploads/merged_video.mp4'
        final_clip.write_videofile(output_path)

        return output_path
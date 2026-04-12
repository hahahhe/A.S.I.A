from diffusers import AudioLDMPipeline, AudioLDM2Pipeline
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import os
import config
import torch

# AudioLDMPipeline 로드 및 GPU 설정
audio_pipe = AudioLDMPipeline.from_pretrained("cvssp/audioldm-m-full", torch_dtype=torch.float16)#.to(audio_device)

def generate_sound_from_caption(caption, duration):
    # 캡션을 바탕으로 오디오 생성 - 수정된 버전
    audio = audio_pipe(caption, num_inference_steps=10, audio_length_in_s=duration).audios[0]
    actual_duration = len(audio) / 16000  # 오디오 길이 계산 (16000은 샘플링 레이트)
    return audio, actual_duration

def add_audio_to_video(video_path, audio_clips_info):
    # 비디오에 오디오 추가 - 수정된 버전
    print('add func: ', video_path, audio_clips_info)
    video_clip = VideoFileClip(video_path)
    print('???')
    audio_clips = []
    for clip_info in audio_clips_info:
        print('clip: ', clip_info)
        audio_clip = AudioFileClip(clip_info['path'])

        if audio_clip.duration > clip_info['duration']:
            audio_clip = audio_clip.subclip(0, clip_info['duration'])

        audio_clip = audio_clip.set_start(clip_info['start_time'])
        audio_clips.append(audio_clip)

    composite_audio = CompositeAudioClip(audio_clips)
    video_clip_with_audio = video_clip.set_audio(composite_audio)

    output_path = os.path.join(config.UPLOAD_FOLDER, f"final.mp4")
    video_clip_with_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return output_path
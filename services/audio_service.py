from typing import Dict, List, Any, TypedDict
import scipy.io.wavfile
import os
from collections import defaultdict
import uuid

class CaptureInfo(TypedDict):
    capture_filename: str
    interval: List[float]
    caption: str
    sound_url: str

class AudioClipInfo(TypedDict):
    class_name: str
    path: str
    start_time: float
    duration: float

# 이미지로부터 캡션 생성
def generate_caption(image_path: str, models: Dict[str, Any]) -> str:
    from PIL import Image
    
    caption_model = models['cpation_model']
    caption_processor = models['caption_processor']

    image = Image.open(image_path)
    prompt = "<grounding>"
    inputs = caption_processor(text=prompt, images=image, return_tensors="pt")

    generated_ids = caption_model.generate(
        pixel_values=inputs["pixel_values"],
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        image_embeds=None,
        image_embeds_position_mask=inputs["image_embeds_position_mask"],
        use_cache=True,
        max_new_tokens=40,
    )
    generated_text = caption_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    processed_text, _ = caption_processor.post_process_generation(generated_text)
    return processed_text

# 캡션을 바탕으로 오디오 생성
def generate_audio_from_caption(caption: str, duration: float, models: Dict[str, Any]) -> tuple:
    audio_pipe = models['audio_pipe']
    audio = audio_pipe(caption, num_inference_steps=10, audio_length_in_s=duration).audios[0]
    actual_duration = len(audio) / 16000  # 오디오 길이 계산 (16000은 샘플링 레이트)

    return audio, actual_duration

# 파일 저장
def save_audio_file(audio, filename: str, upload_folder: str) -> str:
    path = os.path.join(upload_folder, filename)
    scipy.io.wavfile.write(path, rate = 16000, data=audio)

    return path


def process_audio(data: Dict[str, Any], models: Dict[str, Any], upload_folder: str) -> Dict[str, Any]:
    capture_images = data['capture_images']

    audio_file_counts: Dict[str, int] = defaultdict(int)
    audio_clips_info: List[AudioClipInfo] = []

    for class_name in capture_images.keys():
            for capture in capture_images[class_name]:
                image_path = os.path.join(upload_folder, capture['capture_filename'])
                caption = generate_caption(image_path)
                duration = capture['interval'][1] - capture['interval'][0]
                sound_wav, actual_duration = generate_audio_from_caption(caption, duration, models)
                #sound_filename = f"sound_{uuid.uuid4().hex}.wav"
                
                sound_filename = f"{class_name}_{audio_file_counts[class_name]}.wav"
                audio_file_counts[class_name] += 1
                sound_path = save_audio_file(sound_wav, sound_filename, upload_folder)
                #sound_path = sound_path.replace('\\', '/')
                scipy.io.wavfile.write(sound_path, rate=16000, data=sound_wav)

                # 오디오 클립 정보 추가
                audio_clips_info.append({
                    'class': class_name, # 추가
                    'path': sound_path,
                    'start_time': capture['interval'][0],
                    'duration': min(actual_duration, duration),  # 실제 오디오 길이와 요청된 길이 중 작은 값 사용
                })

                capture['caption'] = caption
                capture['sound_url'] = f"/uploads/{sound_filename}"

    return {'audio_clips_info': audio_clips_info, 'capture_images': capture_images}


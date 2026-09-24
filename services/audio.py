from collections import defaultdict
import torch
from diffusers import AudioLDMPipeline

audio_device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("audio device: ", audio_device)

# AudioLDMPipeline 로드 및 GPU 설정
audio_pipe = AudioLDMPipeline.from_pretrained("cvssp/audioldm-m-full", torch_dtype=torch.float16).to(audio_device)
audio_file_counts = defaultdict(int)
id_mapping = {}

def generate_sound_from_caption(caption, duration):
    # 캡션을 바탕으로 오디오 생성 - 수정된 버전
    audio = audio_pipe(caption, num_inference_steps=10, audio_length_in_s=duration).audios[0]
    actual_duration = len(audio) / 16000  # 오디오 길이 계산 (16000은 샘플링 레이트)
    return audio, actual_duration

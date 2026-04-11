import torch
from transformers import AutoProcessor, AutoModelForVision2Seq
from diffusers import AudioLDMPipeline

def load_models():
    # GPU 사용 가능 여부 확인 및 디바이스 설정
    audio_device = 'cuda' if torch.cuda.is_available() else 'cpu'
    other_device = 'cpu'  # 나머지 연산은 CPU에서 수행

    # YOLO 모델 로드 및 CPU 설정
    yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', path='oldfilm.pt').to(other_device)

    # kosmos-2 모델 로드 및 CPU 설정
    caption_model = AutoModelForVision2Seq.from_pretrained("microsoft/kosmos-2-patch14-224").to(other_device)
    caption_processor = AutoProcessor.from_pretrained("microsoft/kosmos-2-patch14-224")

    # AudioLDMPipeline 로드 및 GPU 설정
    audio_pipe = AudioLDMPipeline.from_pretrained("cvssp/audioldm-m-full", torch_dtype=torch.float16).to(audio_device)
    audio_file_counts = defaultdict(int)

    return{
        'yolo': yolo_model,
        'caption_model': caption_model,
        'caption_processor': caption_processor,
        'audio_pipe': audio_pipe,
        'audio_file_counts': audio_file_counts
    }
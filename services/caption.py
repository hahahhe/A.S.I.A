import torch
from PIL import Image
from transformers import AutoProcessor, Kosmos2ForConditionalGeneration

other_device = 'cpu'

device = 'cuda' if torch.cuda.is_available() else 'cpu'
yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', path='oldfilm.pt').to(device)

# kosmos-2 모델 로드 및 CPU 설정
caption_model = Kosmos2ForConditionalGeneration.from_pretrained("microsoft/kosmos-2-patch14-224").to(device)
caption_processor = AutoProcessor.from_pretrained("microsoft/kosmos-2-patch14-224")

print("caption_model: ", device)

def generate_caption_for_image(image_path):
    # 이미지로부터 캡션 생성
    image = Image.open(image_path)
    prompt = "<grounding>"
    inputs = caption_processor(text=prompt, images=image, return_tensors="pt").to(device)
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
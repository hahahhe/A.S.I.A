from flask import Blueprint, request, jsonify, current_app, url_for, Response
#from services.audio_service import process_audio
import os
import config
import requests
import scipy.io.wavfile
import io
from common.video_utils import generate_caption_for_image
from services.audio_service import generate_sound_from_caption, add_audio_to_video
from collections import defaultdict
from diffusers import AudioLDM2Pipeline
import torch

audio_bp = Blueprint('audio', __name__)

audio_file_counts = defaultdict(int)
id_mapping = {}

@audio_bp.route('/process/audio', methods=['POST'])
def process_audio():
    try:
        data = request.json

        capture_images = data['capture_images']

        # 오디오 클립 정보를 저장할 리스트
        audio_clips_info = []
        for class_name in capture_images.keys():
            for capture in capture_images[class_name]:
                image_path = os.path.join(config.UPLOAD_FOLDER, capture['capture_filename'])
                caption = generate_caption_for_image(image_path)
                duration = capture['interval'][1] - capture['interval'][0]
                sound_wav, actual_duration = generate_sound_from_caption(caption, duration)
                #sound_filename = f"sound_{uuid.uuid4().hex}.wav"
                
                sound_filename = f"{class_name}_{audio_file_counts[class_name]}.wav"
                audio_file_counts[class_name] += 1
                sound_path = os.path.join(config.UPLOAD_FOLDER, sound_filename)
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
                capture['sound_url'] = url_for('uploaded_file', filename=sound_filename)

        return jsonify({
            'audio_clips_info': audio_clips_info,
            'capture_images': capture_images
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@audio_bp.route('/getList')
def getList():
    api_key = 'EX2F14a3aOQbQeiqwu9YSbknz7IURVzBUtaeOTIB'

    # 검색할 단어 설정
    search_words = list(audio_file_counts.keys())

    audios = []
    for word in search_words:
        print(f'Searching for sounds with word: {word}')
        # Freesound API를 통해 검색 진행
        url = f"https://freesound.org/apiv2/search/text/?query={word}&fields=id,name,previews&token={api_key}&page_size=5"
        response = requests.get(url)
        data = response.json()

        # 결과에서 오디오 파일의 이름, URL, 및 ID를 추출합니다.
        for idx, sound in enumerate(data['results']):
            custom_id = f"{word}-{idx}"
            audios.append({
                'id': custom_id,  # 사용자 정의 ID 사용
                'name': sound['name'],
                'url': sound['previews']['preview-hq-mp3']
            })
            # 사용자 정의 ID와 원래의 Freesound ID 매핑 저장
            id_mapping[custom_id] = sound['id']

    print(f'Found {len(audios)} sounds')
    # 데이터를 JSON 형식으로 반환합니다.
    return jsonify(audios)

@audio_bp.route('/download')
def download_sound():
    api_key = 'EX2F14a3aOQbQeiqwu9YSbknz7IURVzBUtaeOTIB'

    # 쿼리 매개변수에서 custom_id 추출
    custom_id = request.args.get('soundId')

    # 매핑을 사용하여 원래의 sound_id 찾기
    sound_id = id_mapping.get(custom_id)
    if not sound_id:
        return f'Error: sound ID not found for {custom_id}', 404

    # Freesound API 다운로드 URL
    download_url = f'https://freesound.org/apiv2/sounds/{sound_id}/?token={api_key}'

    # 파일 다운로드 요청
    response = requests.get(download_url, allow_redirects=True)
    sound_info = response.json()

    if response.status_code == 200:
        download_url = sound_info['previews']['preview-lq-mp3']
        download_response = requests.get(download_url)
        # 'effects' 폴더에 파일 저장
        save_folder = 'effects'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        file_extension = download_url.split('.')[-1]
        file_path = os.path.join(save_folder, f'{custom_id}.{file_extension}')
        spath =  os.path.join(f'{custom_id}.{file_extension}')
        with open(file_path, 'wb') as file:
            file.write(download_response.content)
        
        print('패뚜: ', spath)
        return jsonify(spath)
    else:
        return f'Error downloading file: {response.reason}', response.status_code

@audio_bp.route('/generate_audio', methods=['POST'])
def generate_audio():
    # 오디오 생성 모델 초기화
    pipe = AudioLDM2Pipeline.from_pretrained("cvssp/audioldm2", torch_dtype=torch.float16)
    pipe = pipe.to("cuda")

    # 사용자 입력 받기
    text = request.form['text']
    duration = float(request.form['duration'])

    # 오디오 생성
    audio = pipe(text, num_inference_steps=200, audio_length_in_s=duration).audios[0]

    # 오디오를 BytesIO 객체에 저장
    byte_io = io.BytesIO()
    scipy.io.wavfile.write(byte_io, rate=16000, data=audio)
    byte_io.seek(0)  # 파일 읽기 위치를 시작점으로 이동

    return Response(byte_io.getvalue(), mimetype='audio/wav')

@audio_bp.route('/save_audio', methods=['POST'])
def save_audio():

    print('app[saved_folder]: ', config.SAVED_FOLDER)

    # 오디오 데이터와 파일 이름 받기
    audio_data = request.files['audio_data']
    filename = request.form['filename']

    # 오디오 파일 저장
    filepath = os.path.join(config.SAVED_FOLDER, filename)
    audio_data.save(filepath)

    # 저장된 오디오 파일 목록 반환
    path = os.path.join(config.SAVED_FOLDER)
    mp3_files = [f for f in os.listdir(path) if f.endswith('.wav')]
    print('mp3_files: ', mp3_files)

    return jsonify(mp3_files)

@audio_bp.route('/finalize/video', methods=['POST'])
def finalize_video():
    try:
        data = request.json
        labeled_video_path = data['labeled_video_path']
        print('final_label: ', labeled_video_path)
        audio_clips_info = data['audio_clips_info']
        print('final_audio: ', audio_clips_info)
        final_video_path = add_audio_to_video(labeled_video_path, audio_clips_info)

        return jsonify({
            'final_video_url': url_for('uploaded_file', filename=os.path.basename(final_video_path))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
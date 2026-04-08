from flask import Blueprint, request, jsonify, current_app
from services.audio_service import process_audio

audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/process/audio', methods=['POST'])
def process_audio():
    data = request.json

    models = current_app.config['MODELS']
    upload_folder = current_app.config['UPLOAD_FOLDER']

    result = process_audio(data, models, upload_folder)

    return jsonify(result)
from flask import Flask
import config
from models.loader import load_models
from routes.audio_routes import audio_bp
from routes.video_routes import video_bp
from utils.logger import setup_logger

def create_app():

    app = Flask(__name__)

    setup_logger()

    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["SAVED_FOLDER"] = config.SAVED_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    # 모델 로딩
    app.config["MODELS"] = load_models()

    # 라우터 등록
    app.register_blueprint(audio_bp)
    app.register_blueprint(video_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
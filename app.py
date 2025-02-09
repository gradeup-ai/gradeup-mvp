from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from livekit import AccessToken, VideoGrant

app = Flask(__name__)

# 🔹 Подключение к базе данных PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)

# 🔹 Настройка LiveKit
LIVEKIT_URL = "wss://ai-hr-g13ip1bp.livekit.cloud"
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# 🔹 Настройка Deepgram
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_VOICE_MODEL = "aura-asteria-en"  # Пока используем стандартный голос

# 🔹 Модель компании
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    inn = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# 🔹 Модель кандидата
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    position = db.Column(db.String(100))

# 🔹 Модель вакансии
class Vacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50))
    tasks = db.Column(db.Text)
    tools = db.Column(db.Text)
    skills = db.Column(db.Text)
    theoretical_knowledge = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    work_format = db.Column(db.String(50))
    client_industry = db.Column(db.String(100))
    city = db.Column(db.String(100))
    work_time = db.Column(db.String(50))
    benefits = db.Column(db.Text)
    additional_info = db.Column(db.Text)

with app.app_context():
    db.create_all()

# ✅ Главная страница
@app.route('/')
def home():
    return "Привет, Gradeup MVP!"

# ✅ Генерация токена доступа для LiveKit
@app.route('/get_livekit_token', methods=['POST'])
def get_livekit_token():
    try:
        data = request.get_json()
        user_identity = data.get("identity", "candidate")

        token = AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, identity=user_identity)
        grant = VideoGrant(room_join=True, room_list=True)
        token.add_grant(grant)

        jwt_token = token.to_jwt()
        return jsonify({"token": jwt_token})

    except Exception as e:
        return jsonify({"error": "Ошибка генерации токена", "details": str(e)}), 500

# ✅ Генерация речи с Deepgram (TTS)
@app.route('/generate_speech', methods=['POST'])
def generate_speech():
    try:
        data = request.get_json()
        text = data.get("text", "Добрый день! Начнем собеседование.")

        url = "https://api.deepgram.com/v1/speak"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model": DEEPGRAM_VOICE_MODEL
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.content  # Возвращает аудиофайл

    except Exception as e:
        return jsonify({"error": "Ошибка генерации речи", "details": str(e)}), 500

# ✅ Функции для преобразования моделей в JSON
def vacancy_to_dict(vacancy):
    return {c.name: getattr(vacancy, c.name) for c in vacancy.__table__.columns}

def company_to_dict(company):
    return {c.name: getattr(company, c.name) for c in company.__table__.columns}

# ✅ Запуск сервера
if __name__ == '__main__':
    app.run(debug=True, port=5000)

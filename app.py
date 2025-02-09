from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import openai
from deepgram import Deepgram
from livekit import AccessToken, VideoGrant
from livekit.api import RoomServiceClient
from livekit.models import CreateRoomRequest

app = Flask(__name__)

# 🔹 Подключение к БД PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)

# 🔹 API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # GPT-4o
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_VOICE_MODEL = "aura-asteria-en"  # Пока стандартный голос

# 🔹 Подключение к Deepgram
dg_client = Deepgram(DEEPGRAM_API_KEY)

# 🔹 Настройка LiveKit
LIVEKIT_URL = "wss://ai-hr-g13ip1bp.livekit.cloud"
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Создание клиента LiveKit
lk_client = RoomServiceClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

# 🔹 AI-HR Настройки
AI_HR_NAME = "Эмили"
GREETING_PROMPT = f"Здравствуйте! Меня зовут {AI_HR_NAME}, и я — виртуальный рекрутер. Сегодня мы проведем интервью на позицию {{position}} в компании {{company_name}}. Давайте начнем с рассказа о вашем опыте?"
FAREWELL_PROMPT = f"Спасибо за интервью! В ближайшее время вы получите отчет с рекомендациями. Хорошего дня!"

# 🔹 **Модели базы данных**
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    inn = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    city = db.Column(db.String(100))
    position = db.Column(db.String(100))
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    interview_score = db.Column(db.Float, default=0)

class Vacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.Text)
    tasks = db.Column(db.Text)
    theoretical_knowledge = db.Column(db.Text)

with app.app_context():
    db.create_all()

# ✅ **Приветствие AI-HR**
@app.route('/greet/<int:candidate_id>/<int:vacancy_id>', methods=['GET'])
def greet(candidate_id, vacancy_id):
    candidate = Candidate.query.get(candidate_id)
    vacancy = Vacancy.query.get(vacancy_id)
    company = Company.query.get(vacancy.company_id) if vacancy else None

    if not candidate or not vacancy or not company:
        return jsonify({"error": "Кандидат, вакансия или компания не найдены"}), 404

    greeting = GREETING_PROMPT.format(position=vacancy.position, company_name=company.name)
    return jsonify({"message": greeting})

# ✅ **Создание комнаты в LiveKit**
@app.route('/create_room', methods=['POST'])
def create_room():
    try:
        data = request.get_json()
        room_name = data.get("room_name", "interview-room")

        request = CreateRoomRequest(name=room_name)
        room = lk_client.create_room(request)

        return jsonify({"room_url": f"{LIVEKIT_URL}/join/{room.name}"})

    except Exception as e:
        return jsonify({"error": "Ошибка создания комнаты", "details": str(e)}), 500

# ✅ **Генерация токена для подключения к LiveKit**
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

# ✅ **Генерация вопросов AI-HR**
@app.route('/generate_question', methods=['POST'])
def generate_question():
    try:
        data = request.get_json()
        candidate_id = data.get("candidate_id")
        vacancy_id = data.get("vacancy_id")

        candidate = Candidate.query.get(candidate_id)
        vacancy = Vacancy.query.get(vacancy_id)

        if not candidate or not vacancy:
            return jsonify({"error": "Кандидат или вакансия не найдены"}), 404

        prompt = f"""
        Ты — AI-рекрутер по имени {AI_HR_NAME}. Тебе нужно задать кандидату **релевантный вопрос** для оценки его навыков.

        🔹 **Данные вакансии**:
        Должность: {vacancy.position}
        Компания: {Company.query.get(vacancy.company_id).name}
        Навыки: {vacancy.skills}
        Задачи: {vacancy.tasks}
        Теоретические знания: {vacancy.theoretical_knowledge}

        🔹 **Данные кандидата**:
        Должность: {candidate.position}
        Навыки: {candidate.skills}
        Опыт: {candidate.experience}

        Сформулируй **только один** вопрос.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        question = response['choices'][0]['message']['content']
        return jsonify({"question": question})

    except Exception as e:
        return jsonify({"error": "Ошибка генерации вопроса", "details": str(e)}), 500

# ✅ **Распознавание речи с Deepgram (STT)**
@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "Файл аудио не найден"}), 400

        audio_file = request.files['audio']
        url = "https://api.deepgram.com/v1/listen"
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}"
        }
        response = requests.post(url, headers=headers, files={"audio": audio_file})

        return response.json()

    except Exception as e:
        return jsonify({"error": "Ошибка распознавания речи", "details": str(e)}), 500

# ✅ **Запуск сервера**
if __name__ == '__main__':
    app.run(debug=True, port=5000)


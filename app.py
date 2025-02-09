from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests
import openai
from livekit import RoomServiceClient, AccessToken, VideoGrant
from livekit.models import CreateRoomRequest

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
DEEPGRAM_VOICE_MODEL = "aura-asteria-en"  # Используем стандартный голос

# 🔹 Подключение к OpenAI GPT-4o
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 🔹 Создание клиента LiveKit
lk_client = RoomServiceClient(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)

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

# ✅ Приветствие AI-HR
def get_ai_hr_greeting(candidate_name, vacancy, company_name):
    return f"Здравствуйте, {candidate_name}! Меня зовут Эмили, и я – виртуальный HR компании {company_name}. Сегодня мы обсудим вашу квалификацию на позицию {vacancy}. Начнём с небольшой информации о вашем опыте?"

# ✅ Прощание AI-HR
def get_ai_hr_farewell(candidate_name):
    return f"Спасибо, что уделили время на наше собеседование, {candidate_name}. Мы проанализируем ваши ответы, и скоро вы получите рекомендации и дальнейшие шаги. Хорошего дня!"

# ✅ Генерация вопросов AI-HR на основе вакансии и профиля кандидата
def generate_interview_question(candidate, vacancy):
    prompt = f"""
    Ты – виртуальный HR Эмили. Твоя задача – проводить собеседование.
    
    Вакансия: {vacancy.position} в компании {vacancy.company_id}
    Навыки: {vacancy.skills}
    Требуемые знания: {vacancy.theoretical_knowledge}

    Кандидат: {candidate.name}, позиция: {candidate.position}
    Город: {candidate.city}

    Сформулируй релевантный вопрос для собеседования, основываясь на вакансии и профиле кандидата.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# ✅ Создание комнаты в LiveKit
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

# ✅ Распознавание речи через Deepgram (STT)
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

# ✅ Функции для преобразования моделей в JSON
def vacancy_to_dict(vacancy):
    return {c.name: getattr(vacancy, c.name) for c in vacancy.__table__.columns}

def company_to_dict(company):
    return {c.name: getattr(company, c.name) for c in company.__table__.columns}

# ✅ Запуск сервера
if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# 🔹 Подключение к базе данных PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gradeup_db_8l0b_user:kfPPw4BhBttJ5QtTGUfq6UpofZ1G5c3y@dpg-cuk36rggph6c73bn3rbg-a.oregon-postgres.render.com/gradeup_db_8l0b?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  

db = SQLAlchemy(app)

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

# ✅ Создание вакансии
@app.route('/create_vacancy', methods=['POST'])
def create_vacancy():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400

        new_vacancy = Vacancy(**data)
        db.session.add(new_vacancy)
        db.session.commit()
        return jsonify({'message': 'Вакансия создана успешно!', 'vacancy_id': new_vacancy.id}), 201

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Получение всех вакансий
@app.route('/vacancies', methods=['GET'])
def get_vacancies():
    vacancies = Vacancy.query.all()
    return jsonify({'vacancies': [vacancy_to_dict(v) for v in vacancies]}), 200

# ✅ Получение вакансии по ID (исправлено)
@app.route('/vacancy/<int:id>', methods=['GET'])
def get_vacancy(id):
    try:
        vacancy = Vacancy.query.get(id)
        if not vacancy:
            return jsonify({'error': 'Вакансия не найдена'}), 404
        return jsonify(vacancy_to_dict(vacancy)), 200
    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Обновление вакансии
@app.route('/update_vacancy/<int:id>', methods=['PUT'])
def update_vacancy(id):
    try:
        vacancy = Vacancy.query.get(id)
        if not vacancy:
            return jsonify({'error': 'Вакансия не найдена'}), 404

        data = request.get_json()
        for key, value in data.items():
            setattr(vacancy, key, value)

        db.session.commit()
        return jsonify({'message': 'Вакансия обновлена успешно!'}), 200

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Удаление вакансии (исправлено)
@app.route('/delete_vacancy/<int:id>', methods=['DELETE'])
def delete_vacancy(id):
    try:
        vacancy = Vacancy.query.get(id)
        if not vacancy:
            return jsonify({'error': 'Вакансия не найдена'}), 404

        db.session.delete(vacancy)
        db.session.commit()

        return jsonify({'message': 'Вакансия удалена успешно!'}), 200
    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Получение списка компаний
@app.route('/companies', methods=['GET'])
def get_companies():
    companies = Company.query.all()
    return jsonify({'companies': [company_to_dict(c) for c in companies]}), 200

# ✅ Получение информации о компании
@app.route('/company/<int:id>', methods=['GET'])
def get_company(id):
    company = Company.query.get(id)
    if not company:
        return jsonify({'error': 'Компания не найдена'}), 404
    return jsonify(company_to_dict(company)), 200

# ✅ Обновление информации о компании
@app.route('/update_company/<int:id>', methods=['PUT'])
def update_company(id):
    try:
        company = Company.query.get(id)
        if not company:
            return jsonify({'error': 'Компания не найдена'}), 404

        data = request.get_json()
        for key, value in data.items():
            setattr(company, key, value)

        db.session.commit()
        return jsonify({'message': 'Компания обновлена успешно!'}), 200

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Удаление компании
@app.route('/delete_company/<int:id>', methods=['DELETE'])
def delete_company(id):
    try:
        company = Company.query.get(id)
        if not company:
            return jsonify({'error': 'Компания не найдена'}), 404

        db.session.delete(company)
        db.session.commit()
        return jsonify({'message': 'Компания удалена успешно!'}), 200

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Функции для преобразования моделей в JSON
def vacancy_to_dict(vacancy):
    return {c.name: getattr(vacancy, c.name) for c in vacancy.__table__.columns}

def company_to_dict(company):
    return {c.name: getattr(company, c.name) for c in company.__table__.columns}

# ✅ Запуск сервера
if __name__ == '__main__':
    app.run(debug=True, port=5000)

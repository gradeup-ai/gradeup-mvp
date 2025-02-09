from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# 🔹 Обновлённый `DATABASE_URL` (без `sslmode=require`)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gradeup_db_gw2q_user:ssaBqXPAIZi0FMuKgwaSf95G4UDBAWWQ@dpg-cuk2f9d6l47c73c7nv60-a.oregon-postgres.render.com/gradeup_db_gw2q?sslmode=require&connect_timeout=10'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Используется для подписи JWT

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
    city = db.Column(db.String(50))
    position = db.Column(db.String(100))

# 🔹 Создаём таблицы (если их нет)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Привет, Gradeup MVP!"

# ✅ Регистрация компании
@app.route('/register_company', methods=['POST'])
def register_company():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400

        # Проверка дубликатов
        if Company.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Компания с таким email уже зарегистрирована'}), 400
        if Company.query.filter_by(inn=data['inn']).first():
            return jsonify({'error': 'Компания с таким ИНН уже существует'}), 400

        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
        new_company = Company(
            name=data['name'],
            inn=data['inn'],
            description=data.get('description', ''),
            email=data['email'],
            password=hashed_password
        )

        db.session.add(new_company)
        db.session.commit()
        return jsonify({'message': 'Компания зарегистрирована успешно!'}), 201

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Регистрация кандидата
@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    try:
        data = request.get_json()
        if Candidate.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Кандидат уже зарегистрирован'}), 400

        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
        new_candidate = Candidate(
            name=data['name'],
            email=data['email'],
            password=hashed_password,
            city=data.get('city', ''),
            position=data.get('position', '')
        )

        db.session.add(new_candidate)
        db.session.commit()
        return jsonify({'message': 'Кандидат зарегистрирован успешно!'}), 201

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Логин (JWT)
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = Company.query.filter_by(email=data['email']).first() or Candidate.query.filter_by(email=data['email']).first()

        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'message': 'Неверный email или пароль'}), 401

        token = jwt.encode(
            {'email': user.email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        return jsonify({'token': token})
    
    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Пример защищённого маршрута (только с токеном)
@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Токен отсутствует'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except:
        return jsonify({'message': 'Неверный токен'}), 401
    return jsonify({'message': 'Вы авторизованы!'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)




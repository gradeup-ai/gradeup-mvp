from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# Подключение к базе PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gradeup_db_user:73Dm62s8x1XAizInR6XQxT2Jfr4drZun@dpg-cuk0p1dds78s739jsph0-a.oregon-postgres.render.com/gradeup_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Ключ для подписи JWT

db = SQLAlchemy(app)

# Модель компании
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    inn = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Модель кандидата
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50))
    position = db.Column(db.String(100))

# Создание базы данных перед первым запуском
with app.app_context():
    db.create_all()

# Функция для проверки токена (декоратор)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Токен отсутствует'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'message': 'Неверный токен'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return "Привет, Gradeup MVP с авторизацией!"

# ✅ Регистрация компании
@app.route('/register_company', methods=['POST'])
def register_company():
    data = request.get_json()
    if Company.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Компания уже зарегистрирована'}), 400

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

# ✅ Регистрация кандидата
@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json()
    if Candidate.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Кандидат уже зарегистрирован'}), 400

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

# ✅ Логин (JWT)
@app.route('/login', methods=['POST'])
def login():
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

# ✅ Пример защищённого маршрута (только с токеном)
@app.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'Вы авторизованы!'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)



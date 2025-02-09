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
app.config['SECRET_KEY'] = 'supersecretkey'  # Секретный ключ для JWT

# 🔹 Улучшенное подключение к БД (избегаем разрывов соединения)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True
}

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

# 🔹 Создаём таблицы при старте сервера
with app.app_context():
    db.create_all()

# ✅ Главная страница
@app.route('/')
def home():
    return "Привет, Gradeup MVP!"

# ✅ Регистрация компании
@app.route('/register_company', methods=['POST', 'OPTIONS'])
def register_company():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight OK'}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400

        # Проверка на дубликаты
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
        db.session.rollback()  # Откатываем изменения при ошибке
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Регистрация кандидата
@app.route('/register_candidate', methods=['POST', 'OPTIONS'])
def register_candidate():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight OK'}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400

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
        db.session.rollback()
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Авторизация (JWT-токен)
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400

        user = Company.query.filter_by(email=data['email']).first() or Candidate.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Неверный email или пароль'}), 401

        token = jwt.encode({'email': user.email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)},
                           app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})

    except Exception as e:
        return jsonify({'error': 'Ошибка сервера', 'details': str(e)}), 500

# ✅ Проверка JWT-токена
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 403

        try:
            token = token.split(" ")[1]  # "Bearer ТВОЙ_ТОКЕН"
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'], options={"verify_exp": False})
            current_user = Company.query.filter_by(email=data['email']).first() or Candidate.query.filter_by(email=data['email']).first()
            if not current_user:
                return jsonify({'error': 'Недействительный токен'}), 403
        except Exception as e:
            return jsonify({'error': 'Ошибка проверки токена', 'details': str(e)}), 403

        return f(current_user, *args, **kwargs)
    return decorated

# ✅ Защищённый маршрут (доступен только с токеном)
@app.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({'message': 'Вы авторизованы!', 'user_email': current_user.email})

# ✅ Запуск сервера
if __name__ == '__main__':
    app.run(debug=True, port=5000)



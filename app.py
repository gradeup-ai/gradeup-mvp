from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Подключение к облачной базе данных PostgreSQL (замени на свой URL!)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gradeup_db_user:73Dm62s8x1XAizInR6XQxT2Jfr4drZun@dpg-cuk0p1dds78s739jsph0-a.oregon-postgres.render.com/gradeup_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель для хранения компаний
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    inn = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)

# Модель для хранения кандидатов
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    city = db.Column(db.String(50))
    position = db.Column(db.String(100))
    cover_letter = db.Column(db.Text)
    github_links = db.Column(db.Text)  # Храним как строку, потом преобразуем в список

# Создание базы данных перед первым запуском
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Привет, Gradeup MVP с облачной базой PostgreSQL!"

# Регистрация компании (POST)
@app.route('/register_company', methods=['POST'])
def register_company():
    data = request.get_json()
    if not data or 'name' not in data or 'inn' not in data:
        return jsonify({"error": "Некорректные данные"}), 400

    new_company = Company(name=data['name'], inn=data['inn'], description=data.get('description', ''))
    db.session.add(new_company)
    db.session.commit()

    return jsonify({"message": "Компания зарегистрирована успешно!", "company": {"id": new_company.id, "name": new_company.name, "inn": new_company.inn, "description": new_company.description}}), 201

# Получение списка компаний (GET)
@app.route('/companies', methods=['GET'])
def get_companies():
    companies = Company.query.all()
    result = [{"id": c.id, "name": c.name, "inn": c.inn, "description": c.description} for c in companies]
    return jsonify({"companies": result})

# Регистрация кандидата (POST)
@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json()
    if not data or 'name' not in data or 'position' not in data:
        return jsonify({"error": "Некорректные данные"}), 400

    github_links = ', '.join(data.get('github_links', []))  # Преобразуем список в строку

    new_candidate = Candidate(
        name=data['name'],
        age=data.get('age'),
        city=data.get('city', ''),
        position=data['position'],
        cover_letter=data.get('cover_letter', ''),
        github_links=github_links
    )
    db.session.add(new_candidate)
    db.session.commit()

    return jsonify({"message": "Кандидат зарегистрирован успешно!", "candidate": {"id": new_candidate.id, "name": new_candidate.name, "position": new_candidate.position}}), 201

# Получение списка кандидатов (GET)
@app.route('/candidates', methods=['GET'])
def get_candidates():
    candidates = Candidate.query.all()
    result = [{"id": c.id, "name": c.name, "position": c.position, "github_links": c.github_links.split(', ')} for c in candidates]
    return jsonify({"candidates": result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Подключение к базе PostgreSQL (замени на свой URL, если нужно)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gradeup_db_user:73Dm62s8x1XAizInR6XQxT2Jfr4drZun@dpg-cuk0p1dds78s739jsph0-a.oregon-postgres.render.com/gradeup_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель компании
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    inn = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)

# Модель вакансии
class Vacancy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50))  # Джуниор, Мидл, Сеньор
    tasks = db.Column(db.Text)
    tools = db.Column(db.Text)
    skills = db.Column(db.Text)
    theoretical_knowledge = db.Column(db.Text)
    salary_range = db.Column(db.String(50))
    work_format = db.Column(db.String(50))
    client_industry = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    city = db.Column(db.String(50))
    work_time = db.Column(db.String(50))
    benefits = db.Column(db.Text)

# Создание базы данных перед первым запуском
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Привет, Gradeup MVP с облачной базой PostgreSQL!"

# ✅ Создание вакансии (POST /create_vacancy)
@app.route('/create_vacancy', methods=['POST'])
def create_vacancy():
    data = request.get_json()
    
    required_fields = ["company_id", "position", "grade", "tasks", "tools", "skills"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Отсутствуют обязательные поля"}), 400

    new_vacancy = Vacancy(
        company_id=data['company_id'],
        position=data['position'],
        grade=data['grade'],
        tasks=data.get('tasks', ''),
        tools=data.get('tools', ''),
        skills=data.get('skills', ''),
        theoretical_knowledge=data.get('theoretical_knowledge', ''),
        salary_range=data.get('salary_range', ''),
        work_format=data.get('work_format', ''),
        client_industry=data.get('client_industry', ''),
        additional_info=data.get('additional_info', ''),
        city=data.get('city', ''),
        work_time=data.get('work_time', ''),
        benefits=data.get('benefits', '')
    )

    db.session.add(new_vacancy)
    db.session.commit()

    return jsonify({"message": "Вакансия успешно создана!", "vacancy_id": new_vacancy.id}), 201

# ✅ Получение всех вакансий (GET /vacancies)
@app.route('/vacancies', methods=['GET'])
def get_vacancies():
    vacancies = Vacancy.query.all()
    result = [{
        "id": v.id,
        "company_id": v.company_id,
        "position": v.position,
        "grade": v.grade,
        "tasks": v.tasks,
        "tools": v.tools,
        "skills": v.skills,
        "theoretical_knowledge": v.theoretical_knowledge,
        "salary_range": v.salary_range,
        "work_format": v.work_format,
        "client_industry": v.client_industry,
        "additional_info": v.additional_info,
        "city": v.city,
        "work_time": v.work_time,
        "benefits": v.benefits
    } for v in vacancies]
    return jsonify({"vacancies": result}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)


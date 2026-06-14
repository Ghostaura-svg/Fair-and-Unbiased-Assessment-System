from flask import Flask
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.faculty_routes import faculty_bp
from routes.student_routes import student_bp

app = Flask(__name__)
app.secret_key = "fair_assessment_secret_key"

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(faculty_bp)
app.register_blueprint(student_bp)

if __name__ == "__main__":
    app.run(debug=True)
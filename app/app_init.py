from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # ================= CONFIG =================
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        'dev-secret-key'
    )

    # Database setup
    os.makedirs(app.instance_path, exist_ok=True)
    db_path = os.path.join(app.instance_path, 'hospital.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ================= EXTENSIONS =================
    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # ================= BLUEPRINT =================
    from app.app_routes import main
    app.register_blueprint(main)

    # ================= USER LOADER =================
    @login_manager.user_loader
    def load_user(user_id):
        from app.app_models import User
        return db.session.get(User, int(user_id))

    # ================= DATABASE INIT =================
    with app.app_context():
        from app import app_models
        db.create_all()

        from app.app_models import User, Department, Doctor, Patient, Appointment, Treatment

        # Default admin
        if not User.query.filter_by(role='admin').first():
            admin = User(
                name='Admin',
                email='admin@hospital.com',
                role='admin'
            )
            admin.set_password('admin@123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin created")

        # Default departments
        if Department.query.count() == 0:
            departments = [
                Department(name='Cardiology', description='Heart related problems'),
                Department(name='Neurology', description='Brain and nerves'),
                Department(name='Orthopedics', description='Bones and joints'),
                Department(name='Pediatrics', description='Child care'),
                Department(name='Dermatology', description='Skin related issues'),
                Department(name='General Medicine', description='General treatment'),
                Department(name='Psychiatry', description='Mental health care'),
            ]

            db.session.add_all(departments)
            db.session.commit()
            print("✓ Departments created")

    return app
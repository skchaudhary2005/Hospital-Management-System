"""User management CLI for HMS

Usage:
    python scripts/manage_users.py create-defaults
    python scripts/manage_users.py list-doctors
    python scripts/manage_users.py delete-doctor --email doctor@example.com
    python scripts/manage_users.py delete-all-doctors

This script uses the application factory to get a context and perform DB operations.
"""
import argparse
from getpass import getpass
import os
import sys

# Ensure project root is on sys.path so `from app...` imports work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app_init import create_app, db
from app.app_models import User, Doctor


def create_defaults():
    app = create_app()
    with app.app_context():
        created = []
        if not User.query.filter_by(email='admin@hospital.com').first():
            admin = User(name='Admin', email='admin@hospital.com', role='admin')
            admin.set_password('admin@123')
            db.session.add(admin)
            created.append(('admin', admin.email))

        if not User.query.filter_by(email='doctor@hospital.com').first():
            doctor_user = User(name='Dr. Afelis', email='doctor@hospital.com', role='doctor')
            doctor_user.set_password('doctor@123')
            db.session.add(doctor_user)
            db.session.flush()
            doctor = Doctor(user_id=doctor_user.id, specialization='General')
            db.session.add(doctor)
            created.append(('doctor', doctor_user.email))

        if not User.query.filter_by(email='patient@hospital.com').first():
            patient = User(name='John Doe', email='patient@hospital.com', role='patient')
            patient.set_password('patient@123')
            db.session.add(patient)
            created.append(('patient', patient.email))

        if created:
            db.session.commit()
            print('Created users:')
            for role, email in created:
                print(f' - {role}: {email}')
        else:
            print('Default users already exist.')


def list_doctors():
    app = create_app()
    with app.app_context():
        doctors = Doctor.query.all()
        if not doctors:
            print('No doctors found.')
            return
        print('Doctors:')
        for d in doctors:
            u = User.query.get(d.user_id)
            print(f' - {u.name} <{u.email}> (id={d.id}, user_id={d.user_id}, specialization={d.specialization})')


def delete_doctor_by_email(email):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email, role='doctor').first()
        if not user:
            print(f'No doctor found with email {email}')
            return
        # delete doctor and related user
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            db.session.delete(doctor)
        db.session.delete(user)
        db.session.commit()
        print(f'Deleted doctor {user.name} <{user.email}>')


def delete_all_doctors(confirm=False):
    app = create_app()
    with app.app_context():
        doctors = Doctor.query.all()
        if not doctors:
            print('No doctors found.')
            return
        if not confirm:
            ans = input(f'Are you sure you want to delete ALL doctors ({len(doctors)})? Type YES to confirm: ')
            if ans != 'YES':
                print('Aborted.')
                return
        for d in doctors:
            user = User.query.get(d.user_id)
            if d:
                db.session.delete(d)
            if user:
                db.session.delete(user)
        db.session.commit()
        print('All doctors deleted.')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('create-defaults')
    sub.add_parser('list-doctors')

    p = sub.add_parser('delete-doctor')
    p.add_argument('--email', '-e', required=True)

    sub.add_parser('delete-all-doctors')

    args = parser.parse_args()
    if args.cmd == 'create-defaults':
        create_defaults()
    elif args.cmd == 'list-doctors':
        list_doctors()
    elif args.cmd == 'delete-doctor':
        delete_doctor_by_email(args.email)
    elif args.cmd == 'delete-all-doctors':
        delete_all_doctors()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
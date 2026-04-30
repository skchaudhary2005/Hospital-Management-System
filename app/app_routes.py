from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_login import login_user, current_user,login_required
from datetime import date
from app.app_forms import LoginForm, SearchForm,AddDoctorForm, RegisterForm, AppointmentForm, AddPatientForm,UpdateProfileForm
from app.app_models import User, Doctor, Patient ,Appointment
from app.app_init import db

# ================= INIT =================
main = Blueprint('main', __name__)

# ================= HOME =================
@main.route('/')
def home():
    return redirect(url_for('main.login'))

# ================= AUTH =================
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        print("FORM OK")   # 🔥 debug

        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists", "danger")
            return redirect(url_for('main.register'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            role='patient'
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()   # user.id मिलेगा

        patient = Patient(user_id=user.id)   # 🔥 create           patient
        db.session.add(patient)

        db.session.commit()

        flash("Registration successful!", "success")
        return redirect(url_for('main.login'))

    else:
        print(form.errors)   # 🔥 important

    return render_template("register.html", form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        print("FORM VALID:", form.validate_on_submit())
        print("ERRORS:", form.errors)
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)

            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('main.doctor_dashboard'))
            else:
                return redirect(url_for('main.patient_dashboard'))

        flash("Invalid email or password", "danger")

    return render_template("login.html", form=form)

# ================= ADMIN =================
@main.route('/admin')
def admin_dashboard():
    total_patients = User.query.filter_by(role='patient').count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()

    stats = {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointments
    }

    return render_template("admin_dashboard.html", stats=stats)


@main.route('/add-doctor', methods=['GET', 'POST'])
def add_doctor():
    form = AddDoctorForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists", "danger")
            return redirect(url_for('main.add_doctor'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            role='doctor'
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()

        doctor = Doctor(
            user_id=user.id,
            specialization=form.specialization.data
        )

        db.session.add(doctor)
        db.session.commit()

        flash("Doctor added successfully", "success")
        return redirect(url_for('main.manage_doctors'))

    return render_template("admin_add_doctor.html", form=form)


@main.route('/manage-doctors')
def manage_doctors():
    doctors = Doctor.query.all()
    return render_template("admin_doctors.html", doctors=doctors)

@main.route('/add-patient', methods=['GET', 'POST'])
def add_patient():
    form = AddPatientForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists", "danger")
            return redirect(url_for('main.add_patient'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            role='patient'
        )
        user.set_password(form.password.data)

        # 🔥 IMPORTANT PART
        db.session.add(user)
        db.session.flush()   # user.id generate

        from app.app_models import Patient
        patient = Patient(user_id=user.id)

        db.session.add(patient)
        db.session.commit()

        flash("Patient added successfully!", "success")
        return redirect(url_for('main.manage_patients'))

    return render_template("admin_add_patient.html", form=form)

@main.route('/manage-patients')
def manage_patients():
    patients = User.query.filter_by(role='patient').all()
    return render_template("admin_patients.html", patients=patients)


@main.route('/manage-appointments')
def manage_appointments():
    appointments = Appointment.query.all()
    return render_template("admin_appointments.html", appointments=appointments)

# ================= APPOINTMENT =================
@main.route('/book-appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    form = AppointmentForm()

    from app.app_models import Doctor, Appointment

    # dropdown populate
    form.doctor.choices = [(d.id, d.user.name) for d in Doctor.query.all()]

    if form.validate_on_submit():
        try:
            patient = current_user.patient

            if not patient:
                flash("Patient profile not found", "danger")
                return redirect(url_for('main.patient_dashboard'))

            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=form.doctor.data,
                date=form.date.data,
                time=form.time.data,
                reason=form.reason.data
            )

            db.session.add(appointment)
            db.session.commit()

            flash("Appointment booked successfully!", "success")
            return redirect(url_for('main.patient_dashboard'))

        except Exception as e:
            print("ERROR:", e)
            flash("Something went wrong", "danger")

    else:
        print("FORM ERRORS:", form.errors)

    return render_template("patient_book_appointment.html", form=form)

# ================= SEARCH DOCTORS =================
from app.app_forms import SearchForm

@main.route('/search-doctors', methods=['GET', 'POST'])
def search_doctors():
    form = SearchForm()
    doctors = []

    if form.validate_on_submit():
        query = form.search_query.data

        if form.search_by.data == 'name':
            doctors = Doctor.query.join(User).filter(User.name.ilike(f"%{query}%")).all()
        elif form.search_by.data == 'specialization':
            doctors = Doctor.query.filter(Doctor.specialization.ilike(f"%{query}%")).all()
        elif form.search_by.data == 'email':
            doctors = Doctor.query.join(User).filter(User.email.ilike(f"%{query}%")).all()

    return render_template("patient_search_doctors.html", form=form, doctors=doctors)

# ================= EXTRA (for template buttons) =================

@main.route('/doctor-patients/<int:doctor_id>')
@login_required
def doctor_patients(doctor_id):

    from app.app_models import Doctor

    # 🔐 role check
    if current_user.role != "doctor":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    if not doctor:
        flash("Doctor profile not found", "danger")
        return redirect(url_for('main.login'))

    # 🔐 ownership check
    if doctor.id != doctor_id:
        flash("Unauthorized", "danger")
        return redirect(url_for('main.doctor_dashboard'))

    # 🔥 👉 YAHAN ADD KARNA HAI
    patients = list({
        appt.patient.id: appt.patient
        for appt in doctor.appointments
        if appt.patient is not None
    }.values())

    return render_template(
        "doctor_patients.html",
        patients=patients
    )
@main.route('/delete-doctor/<int:doctor_id>')
@login_required
def delete_doctor(doctor_id):

    # 🔐 only admin allowed
    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    from app.app_models import Doctor

    doctor = Doctor.query.get(doctor_id)

    # ❗ doctor exist check
    if not doctor:
        flash("Doctor not found", "danger")
        return redirect(url_for('main.manage_doctors'))

    # 🚨 IMPORTANT: check appointments
    if doctor.appointments:
        flash("Cannot delete doctor with existing appointments", "danger")
        return redirect(url_for('main.manage_doctors'))

    db.session.delete(doctor)
    db.session.commit()

    flash("Doctor deleted successfully", "success")
    return redirect(url_for('main.manage_doctors'))


@main.route('/delete-patient/<int:patient_id>')
@login_required
def delete_patient(patient_id):

    # 🔐 only admin
    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    patient = User.query.filter_by(id=patient_id, role='patient').first()

    if not patient:
        flash("Patient not found", "danger")
        return redirect(url_for('main.manage_patients'))

    db.session.delete(patient)
    db.session.commit()

    flash("Patient deleted successfully", "success")

    return redirect(url_for('main.manage_patients'))

# ================= DASHBOARDS =================
@main.route('/doctor', methods=['GET', 'POST'])
@login_required
def doctor_dashboard():

    # 🔐 ROLE CHECK
    if current_user.role != "doctor":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    from app.app_models import Doctor, Appointment, Treatment
    

    # 👨‍⚕️ Doctor fetch
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    if not doctor:
        flash("Doctor profile not found", "danger")
        return redirect(url_for('main.login'))

    # 📅 All appointments
    appointments = Appointment.query.filter_by(
        doctor_id=doctor.id
    ).all()

    

    today = date.today()

    today_appointments = [
    appt for appt in appointments
    if appt.date == today
    ]   

    # 👥 Unique patients
    patients = list({
        appt.patient.id: appt.patient
        for appt in appointments
        if appt.patient
    }.values())

    treatments = Treatment.query.filter_by(
    doctor_id=doctor.id
    ).all()

    # ================= POST (ADD TREATMENT) =================
    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        diagnosis = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        notes = request.form.get("notes")

        # ❗ Validation
        if not patient_id:
            flash("Please select patient", "danger")
            return redirect(url_for('main.doctor_dashboard'))

        # 🔍 Latest appointment find
        appointment = Appointment.query.filter_by(
            patient_id=patient_id,
            doctor_id=doctor.id
        ).order_by(Appointment.id.desc()).first()

        if not appointment:
            flash("No appointment found for this patient", "danger")
            return redirect(url_for('main.doctor_dashboard'))

        # 💊 Create treatment
        treatment = Treatment(
            appointment_id=appointment.id,
            patient_id=patient_id,
            doctor_id=doctor.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )

        db.session.add(treatment)

        # 🔥 Update status
        appointment.status = "Completed"

        db.session.commit()

        flash("Treatment added successfully", "success")
        return redirect(url_for('main.doctor_dashboard'))

    # ================= GET =================
    return render_template(
        "doctor_dashboard.html",
        doctor_name=current_user.name,
        appointments=appointments,
        patients=patients,
        today_appointments=today_appointments,
        treatments=treatments 
    )

@main.route('/doctor-appointments')
@login_required
def doctor_appointments():

    # 🔐 ROLE CHECK
    if current_user.role != "doctor":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    from app.app_models import Doctor, Appointment

    # 👨‍⚕️ current doctor find करो
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    if not doctor:
        flash("Doctor profile not found", "danger")
        return redirect(url_for('main.login'))

    # 📅 appointments fetch करो
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()

    return render_template(
        "doctor_appointments.html",
        appointments=appointments
    )

@main.route('/edit-schedule', methods=['GET', 'POST'])
@login_required
def edit_schedule():

    if current_user.role != "doctor":
        return redirect(url_for('main.login'))

    return "Schedule feature coming soon"

# ============ ADD TREATMENT ============
@main.route('/add-treatment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def add_treatment(appointment_id):

    from app.app_models import Appointment, Treatment, Doctor
    from app.app_forms import TreatmentForm

    # 🔐 ROLE CHECK
    if current_user.role != "doctor":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    # 📅 appointment fetch
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        flash("Appointment not found", "danger")
        return redirect(url_for('main.doctor_dashboard'))

    # 👨‍⚕️ doctor fetch
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    if not doctor:
        flash("Doctor profile not found", "danger")
        return redirect(url_for('main.login'))

    # 🔐 ownership check
    if appointment.doctor_id != doctor.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.doctor_dashboard'))

    form = TreatmentForm()

    patients = list({appt.patient.id: appt.patient for appt in doctor.appointments}.values())
    form.patient.choices = [(p.id, p.user.name) for p in patients]

    if form.validate_on_submit():
        treatment = Treatment(
            appointment_id=appointment.id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            diagnosis=form.diagnosis.data,
            prescription=form.prescription.data,
            notes=form.notes.data
        )

        db.session.add(treatment)

        # 🔥 mark complete
        appointment.status = "Completed"

        db.session.commit()

        flash("Treatment added successfully", "success")
        return redirect(url_for('main.doctor_appointments'))

    return render_template("doctor_add_treatment.html", form=form)
@main.route('/patient')
@login_required
def patient_dashboard():
    from app.app_models import Appointment, Department

    patient = current_user.patient

    appointments = []
    if patient:
        appointments = Appointment.query.filter_by(
            patient_id=patient.id
        ).all()

    departments = Department.query.all()

    return render_template(
        "patient_dashboard.html",
        appointments=appointments,
        departments=departments
    )
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_patient_profile():
    from app.app_forms import UpdateProfileForm

    form = UpdateProfileForm()

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data

        db.session.commit()
        flash("Profile updated successfully", "success")

        return redirect(url_for('main.patient_dashboard'))

    # pre-fill form data
    form.name.data = current_user.name
    form.email.data = current_user.email

    return render_template("patient_edit_profile.html", form=form)

# ✅ ADD HERE
@main.route('/patient-appointments')
@login_required
def patient_appointments():
    patient = current_user.patient

    if not patient:
        flash("Patient profile not found", "danger")
        return redirect(url_for('main.patient_dashboard'))

    appointments = Appointment.query.filter_by(
        patient_id=patient.id
    ).all()

    return render_template(
        "patient_appointments.html",
        appointments=appointments
    )

@main.route('/cancel-appointment/<int:appointment_id>')
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)

    if appointment and appointment.patient.user_id == current_user.id:
        appointment.status = "Cancelled"
        db.session.commit()
        flash("Appointment cancelled", "success")

    return redirect(url_for('main.patient_dashboard'))
@main.route('/patient-history/<int:patient_id>')
@login_required
def patient_history(patient_id):
    from app.app_models import Treatment, Patient

    # 🔐 only patient allowed
    if current_user.role != "patient":
        flash("Access denied", "danger")
        return redirect(url_for('main.login'))

    # 👤 patient fetch
    patient = Patient.query.get(patient_id)

    if not patient:
        flash("Patient not found", "danger")
        return redirect(url_for('main.patient_dashboard'))

    # 🔐 ownership check
    if current_user.patient.id != patient_id:
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.patient_dashboard'))

    # 📄 treatments
    treatments = Treatment.query.filter_by(patient_id=patient.id).all()

    return render_template(
        "patient_medical_history.html",
        treatments=treatments
    )
@main.route('/complete-appointment/<int:appointment_id>')
@login_required
def complete_appointment(appointment_id):

    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        flash("Appointment not found", "danger")
        return redirect(url_for('main.doctor_dashboard'))

    appointment.status = "Completed"
    db.session.commit()

    flash("Appointment marked as completed", "success")
    return redirect(url_for('main.doctor_appointments'))
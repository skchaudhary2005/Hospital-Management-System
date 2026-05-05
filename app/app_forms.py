from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.app_models import User


# ================= LOGIN =================
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


# ================= REGISTER =================
class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=3)
    ])

    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])

    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")


# ================= ADD DOCTOR =================
class AddDoctorForm(FlaskForm):
    name = StringField('Doctor Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])

    specialization = SelectField('Specialization', choices=[
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('dermatology', 'Dermatology'),
        ('general', 'General Medicine'),
        ('psychiatry', 'Psychiatry'),
    ])

    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Add Doctor")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already exists.")


# ================= EDIT DOCTOR =================
class EditDoctorForm(FlaskForm):
    name = StringField('Doctor Name', validators=[DataRequired(), Length(min=3)])
    email = StringField('Email', validators=[DataRequired(), Email()])

    password = PasswordField('Password (optional)', validators=[
        Length(min=6)
    ])

    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('password')
    ])

    submit = SubmitField("Update Doctor")


# ================= APPOINTMENT =================
class AppointmentForm(FlaskForm):
    doctor = SelectField("Select Doctor", coerce=int)

    date = DateField("Date", validators=[DataRequired()])
    time = TimeField("Time", validators=[DataRequired()])

    reason = TextAreaField('Reason for Visit', validators=[
        DataRequired(),
        Length(min=10)
    ])

    submit = SubmitField("Book Appointment")


# ================= TREATMENT =================
class TreatmentForm(FlaskForm):
    patient = SelectField(
        "Select Patient",
        coerce=int,
        validators=[DataRequired()]
    )

    diagnosis = TextAreaField(
        "Diagnosis",
        validators=[DataRequired(), Length(min=5, max=500)]
    )

    prescription = TextAreaField(
        "Prescription",
        validators=[DataRequired(), Length(min=5, max=500)]
    )

    notes = TextAreaField(
        "Notes",
        validators=[Length(max=500)]
    )

    submit = SubmitField("Save Treatment")


# ================= PROFILE =================
class UpdateProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=3)])
    email = StringField('Email', validators=[DataRequired(), Email()])

    def validate_email(self, field):
        from flask_login import current_user
        if User.query.filter(User.email == field.data, User.id != current_user.id).first():
            raise ValidationError("Email already in use.")


# ================= SEARCH =================
class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[DataRequired()])

    search_by = SelectField('Search By', choices=[
        ('name', 'Name'),
        ('specialization', 'Specialization'),
        ('email', 'Email')
    ])

    submit = SubmitField("Search")


class AddPatientForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Add Patient")
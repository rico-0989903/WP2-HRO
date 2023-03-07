import os
import sqlite3
import qrcode
from flask import Flask, render_template, jsonify, request, url_for, make_response, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from sqlalchemy import update
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_wtf import FlaskForm

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__name__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'hro.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'NoOneWillEverGuessMySecretKey'

db = SQLAlchemy(app)
ma = Marshmallow(app)

app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return gebruikers.query.get(int(user_id))

#Database models
class Student(db.Model):
    studentnummer = db.Column(db.Integer, primary_key=True, unique=True)
    naam = db.Column(db.String(150), nullable=False)
    klasinschrijvingen = db.relationship('KlasInschrijving', backref='klascodetest ', lazy=True)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='inschrijving1', lazy=True)


class Docent(db.Model):
    docent_id = db.Column(db.Integer, primary_key=True, unique=True)
    naam = db.Column(db.String(150), nullable=False)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='inschrijving2', lazy=True)


class Klas(db.Model):
    klascode = db.Column(db.String(150), primary_key=True, nullable=False)
    slc_docent = db.Column(db.String(150))
    klasinschrijvingen = db.relationship('KlasInschrijving', backref='studenten', lazy=True)

class Les(db.Model):
    les_id = db.Column(db.Integer, primary_key=True, nullable=False)
    vak = db.Column(db.String(150), nullable=False)
    datum = db.Column(db.DateTime, nullable=False)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='inschrijving3', lazy=True)

class KlasInschrijving(db.Model):
    studentnummer = db.Column(db.Integer, db.ForeignKey('student.studentnummer'), primary_key=True, nullable=False)
    klascode = db.Column(db.Integer, db.ForeignKey('klas.klascode'), primary_key=True, nullable=False)

class LesInschrijving(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    studentnummer = db.Column(db.Integer, db.ForeignKey('student.studentnummer'), nullable=False)
    docent_id = db.Column(db.Integer, db.ForeignKey('docent.docent_id'), nullable=False)
    les_id = db.Column(db.Integer, db.ForeignKey('les.les_id'), nullable=False)
    aanwezigheid_check = db.Column(db.Integer, nullable=False)
    afwezigheid_rede = db.Column(db.String(200), nullable=True)

class gebruikers(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

#Marshmellow schemas
class StudentSchema(ma.Schema):
    studentnummer = fields.String()
    naam = fields.String()

class DocentSchema(ma.Schema):
    docent_id = fields.Integer()
    naam = fields.String()

class KlasSchema(ma.Schema):
    klascode = fields.String()
    slc_docent = fields.String()

class LesSchema(ma.Schema):
    les_id = fields.Integer()
    vak = fields.String()
    datum = fields.DateTime()

class KlasInschrijvingSchema(ma.Schema):
    studentnummer = fields.Nested(StudentSchema)
    klascode = fields.Nested(KlasSchema)

class LesInschrijvingSchema(ma.Schema):
    id = fields.Integer()
    studentnummer = fields.Nested(StudentSchema)
    docent_id = fields.Nested(DocentSchema)
    les_id = fields.Nested(LesSchema)
    aanwezigheid_check = fields.Integer()
    afwezigheid_rede = fields.String()

class gebruikersSchema(ma.Schema):
    class meta:
        fields = ('id', 'username', 'password')


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=5, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = gebruikers.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=5, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login" , methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = gebruikers.query.filter_by(username=form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('home'))

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = gebruikers(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route("/home", methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route("/lessen")
@login_required
def lessen():
    return render_template('lessen.html')

@app.route("/docenten")
@login_required
def docenten():
    docenten = Docent.query.all()
    result = DocentSchema.dump(docenten)
    type(docenten)
    return render_template('docenten.html', result = result)

@app.route("/klassen")
@login_required
def klassen():
    return render_template('klassen.html')

@app.route("/klas/<les>", methods = ['POST', 'GET'])
@login_required
def klas(les):
    img = qrcode.make(f"http://127.0.0.1:5000/les/{les}")
    img.save('static/qr.png')
    img = url_for('static', filename='qr.png')
    return render_template('qrcode.html', img=img, les=les)

@app.route("/les/<les>")
@login_required
def aanwezigheid(les):
    return render_template('form.html', les=les)

@app.route("/test", methods = ['POST','GET'])
@login_required
def test():
    studenten = aanwezig.query.order_by(aanwezig.aanwezigheid).all()
    result= students_schema.dump(studenten)
    return jsonify(result)

@app.route("/data", methods = ['POST', 'GET', 'PUT'])
@login_required
def data():
    naam = request.json['naam']
    data = aanwezig.query.filter_by(naam = naam).first()
    print(data)
    data.aanwezigheid=request.json['aanwezigheid']
    db.session.commit()
    return jsonify("Gelukt")

if __name__ == '__main__':
    app.run(host="localhost", debug=True)
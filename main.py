import os
import qrcode
from datetime import datetime
from flask import Flask, render_template, jsonify, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask_login import UserMixin, LoginManager
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
    klasinschrijvingen = db.relationship('KlasInschrijving', backref='student', lazy='dynamic')
    lesinschrijvingen = db.relationship('LesInschrijving', backref='student', lazy=True)


class Docent(db.Model):
    docent_id = db.Column(db.Integer, primary_key=True, unique=True)
    naam = db.Column(db.String(150), nullable=False)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='docent', lazy=True)

    def __init__(self, docent_id, naam):
        self.docent_id = docent_id
        self.naam = naam

class Klas(db.Model):
    klascode = db.Column(db.String(150), primary_key=True, nullable=False)
    slc_docent = db.Column(db.String(150))
    klasinschrijvingen = db.relationship('KlasInschrijving', backref='klas', lazy=True)

class Vak(db.Model):
    vak_id = db.Column(db.Integer, primary_key=True, nullable=False)
    vak = db.Column(db.String(150), nullable=False)
    les = db.relationship('Les', backref='vak1', lazy=True)

class Les(db.Model):
    les_id = db.Column(db.Integer, primary_key=True, nullable=False)
    vak_id = db.Column(db.Integer, db.ForeignKey('vak.vak_id'), nullable=False)
    datum = db.Column(db.DateTime, nullable=False)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='les', lazy=True)

class KlasInschrijving(db.Model):
    klasinschrijving_id = db.Column(db.Integer, primary_key=True, nullable=False)
    studentnummer = db.Column(db.Integer, db.ForeignKey('student.studentnummer'), nullable=False)
    klascode = db.Column(db.Integer, db.ForeignKey('klas.klascode'), nullable=False)

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
    rights = db.Column(db.String(20), nullable=False)

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

class VakSchema(ma.Schema):
    vak_id = fields.Integer()
    vak = fields.String()

class LesSchema(ma.Schema):
    les_id = fields.Integer()
    vak_id = fields.Nested(VakSchema)
    datum = fields.DateTime()

class KlasInschrijvingSchema(ma.Schema):
    klasInschrijving_id = fields.Integer()
    studentnummer = fields.Nested(StudentSchema)
    klascode = fields.Nested(KlasSchema)

class LesInschrijvingSchema(ma.Schema):
    id = fields.Integer()
    studentnummer = fields.Nested(StudentSchema)
    docent_id = fields.Nested(DocentSchema)
    les_id = fields.Nested(LesSchema)
    aanwezigheid_check = fields.Integer()
    afwezigheid_rede = fields.String()

student_schema = StudentSchema(many=True)
docent_schema = DocentSchema(many=True)
klas_schema = KlasSchema(many=True)
les_schema = LesSchema(many=True)
klasinschrijving_schema = KlasInschrijvingSchema(many=True)
lesinschrijving_schema = LesInschrijvingSchema(many=True)


class gebruikersSchema(ma.Schema):
    class meta:
        fields = ('id', 'username', 'password', 'rights')


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

@app.before_request
def before_request():
    if "user" not in session and request.endpoint not in ['login', 'register', 'static', 'index']:
        return redirect(url_for('login'))

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route("/login" , methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = gebruikers.query.filter_by(username=form.username.data).first()
        if user:
            if user.password == form.password.data:
                session['user'] = user.username
                check_rights = gebruikers.query.filter_by(username=user.username).first()
                if check_rights.rights == "True":
                    session['rights'] = True
                else:
                    session['rights'] = False
                return redirect(url_for('home'))
            else:
                error = "Invalid username or password"
                return render_template('login.html', form=form, error=error)
        else:
            error = "Invalid username or password"
            return render_template('login.html', form=form, error=error)
        
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        new_user = gebruikers(username=form.username.data, password=form.password.data, rights="False")
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/lessen")
def lessen():
    return render_template('lessen.html')

@app.route("/getlessen", methods = ['GET'])
def getlessen():
    lessen = Les.query.all()
    lesresult = les_schema.dump(lessen)
    return jsonify(lesresult)

@app.route("/addlesson", methods = ['POST'])
def addlesson():
    datetimeformat = '%Y-%m-%dT%H:%M'
    print(f"Nieuwe les! Vak: {request.json['vak']}, Datum: {request.json['datum']}")
    newlesson = Les(vak=request.json['vak'], datum=datetime.strptime(request.json['datum'], datetimeformat))
    db.session.add(newlesson)
    db.session.commit()

@app.route("/docenten", methods = ['POST', 'GET'])
def docenten():
    return render_template('docenten.html')

@app.route("/getdocenten", methods = ["GET"])
def getdocenten():
    docenten = Docent.query.all()
    result = docent_schema.dump(docenten)
    return jsonify(result)

@app.route("/klassen")
def klassen():
    return render_template('klassen.html')



@app.route("/klas/<klas>/studenten", methods = ['POST', 'GET'])
def klas(klas):
    tests = KlasInschrijving.query.filter_by(klascode = str(klas)).all()
    studenten = []
    for test in tests:
        case = {"naam": test.student.naam, "studentnummer": test.student.studentnummer}
        studenten.append(case)
    return jsonify(studenten)

@app.route("/lessen/<les>", methods = ['POST', 'GET'])
def les(les):
    img = qrcode.make(f"http://127.0.0.1:5000/les/{les}")
    img.save('static/qr.png')
    img = url_for('static', filename='qr.png')
    return render_template('qrcode.html', img=img, les=les)

@app.route("/les/<les>")
def aanwezigheid(les):
    return render_template('form.html', les=les)

@app.route("/test", methods = ['POST','GET'])
def test():
    studenten = aanwezig.query.order_by(aanwezig.aanwezigheid).all()
    result= students_schema.dump(studenten)
    return jsonify(result)

@app.route("/data", methods = ['POST', 'GET', 'PUT'])
def data():
    naam = request.json['naam']
    data = aanwezig.query.filter_by(naam = naam).first()
    print(data)
    data.aanwezigheid=request.json['aanwezigheid']
    db.session.commit()
    return jsonify("Gelukt")

if __name__ == '__main__':
    app.run(host="localhost", debug=True)
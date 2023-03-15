import os
import qrcode
from datetime import datetime
from flask import Flask, render_template, jsonify, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask_login import UserMixin, LoginManager
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash

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
    username = db.Column(db.String(20), db.ForeignKey('student.studentnummer') ,nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
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

class gebruikersSchema(ma.Schema):
    id = fields.Integer()
    username = fields.Nested(StudentSchema)
    password = fields.String()
    rights = fields.String()

student_schema = StudentSchema(many=True)
docent_schema = DocentSchema(many=True)
klas_schema = KlasSchema(many=True)
les_schema = LesSchema(many=True)
klasinschrijving_schema = KlasInschrijvingSchema(many=True)
lesinschrijving_schema = LesInschrijvingSchema(many=True)
gebruikers_schema = gebruikersSchema(many=True)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=150)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=150)], render_kw={"placeholder": "Password"})

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

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = gebruikers.query.filter_by(username=form.username.data).first()
        user = Student.query.filter_by(studentnummer=form.username.data).first()
        if existing_user is None:
            if user:
                hashed_password = generate_password_hash(form.password.data, method='sha256')
                new_user = gebruikers(username=form.username.data, password=hashed_password, rights="False")
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            else:
                error = "No valid Studentnummer"
                return render_template('register.html', form=form, error=error)
        else:
            error = "Username already exists"
            return render_template('register.html', form=form, error=error)
        
    return render_template('register.html', form=form)

@app.route("/login" , methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = gebruikers.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
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

@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/lessen")
def lessen():
        return render_template('lessen.html')

@app.route("/getstudentlessen", methods = ['POST', 'GET'])
def getstudentlessen():
    tests = LesInschrijving.query.filter_by(studentnummer = session['user']).all()

    lessen = []
    for test in tests:
        case = {"id": test.id, "studentnummer": test.student.studentnummer, "docent_id": test.docent.docent_id,
                "les_id": test.les.les_id, "aanwezigheid": test.aanwezigheid_check,
                "afwezigheid_reden": test.afwezigheid_rede, "vak_id": test.les.vak_id, "datum": test.les.datum, "vak": Vak.query.filter_by(vak_id = test.les.vak_id).first().vak}
        lessen.append(case)
    return jsonify(lessen)

@app.route("/getlessen", methods = ['GET'])
def getlessen():
    if session['rights'] == True:
        lessen = Les.query.all()
        lesresult = les_schema.dump(lessen)
        return jsonify(lesresult)
    else:
        return "Jij hebt geen recht"

@app.route("/addlesson", methods = ['POST'])
def addlesson():
    if session['rights'] == True:
        datetimeformat = '%Y-%m-%dT%H:%M'
        print(f"Nieuwe les! Vak: {request.json['vak']}, Datum: {request.json['datum']}")
        newlesson = Les(vak=request.json['vak'], datum=datetime.strptime(request.json['datum'], datetimeformat))
        db.session.add(newlesson)
        db.session.commit()
        return "Les toegevoegd"
    else:
        return "Jij hebt geen recht"

@app.route("/docenten", methods = ['POST', 'GET'])
def docenten():
    if session['rights'] == True:
        return render_template('docenten.html')
    else:
        return "Jij hebt geen recht"

@app.route("/getdocenten", methods = ["POST", "GET"])
def getdocenten():
    if session['rights'] == True:
        docenten = Docent.query.all()
        result = docent_schema.dump(docenten)
        return jsonify(result)
    else:
        return "Jij hebt geen recht"

@app.route("/klassen")
def klassen():
    if session['rights'] == True:
        return render_template('klassen.html')
    else:
        return "Jij hebt geen recht"
    
@app.route("/klas/<klas>/studenten")
def klas(klas):
    return render_template('studenten.html', klas=klas)

@app.route("/<klas>/getstudenten", methods = ['POST', 'GET'])
def getstudenten(klas):
    tests = KlasInschrijving.query.filter_by(klascode = str(klas)).all()
    studenten = []
    for test in tests:
        case = {"naam": test.student.naam, "studentnummer": test.student.studentnummer}
        studenten.append(case)
    return jsonify(studenten)

@app.route("/lessen/<les>", methods = ['POST', 'GET'])
def les(les):
    if session['rights'] == True:
        img = qrcode.make(f"http://127.0.0.1:5000/les/{les}")
        img.save('static/qr.png')
        img = url_for('static', filename='qr.png')
        return render_template('qrcode.html', img=img, les=les)
    else:
        return "Jij hebt geen recht"

@app.route("/les/<les>/aanwezigheid")
def aanwezigheid(les):
    tests = Les.query.filter_by(les_id = les).first()
    lesnaam = tests.vak1.vak
    les_id = tests.les_id
    return render_template('aanwezigheid.html', lesnaam=lesnaam, les_id=les_id)

@app.route("/les/<les>/getaanwezigheid", methods = ['POST', 'GET'])
def lesaanwezigheid(les):
    tests = LesInschrijving.query.filter_by(les_id = str(les)).all()
    aanwezigheid = []
    for test in tests:
        case = {"naam": test.student.naam, "studentnummer": test.student.studentnummer, "aanwezigheid": test.aanwezigheid_check, "afwezigheid_reden": test.afwezigheid_rede}
        aanwezigheid.append(case)
    return jsonify(aanwezigheid)

# @app.route("/les/<les>")
# def aanwezigheid(les):
#     if session['rights'] == True:
#         return render_template('form.html', les=les)
#     else:
#         return "Jij hebt geen recht"

# @app.route("/test", methods = ['POST','GET'])
# def test():
#     if session['rights'] == True:
#         studenten = aanwezig.query.order_by(aanwezig.aanwezigheid).all()
#         result= students_schema.dump(studenten)
#         return jsonify(result)
#     else:
#         return "Jij hebt geen recht"

# @app.route("/data", methods = ['POST', 'GET', 'PUT'])
# def data():
#     if session['rights'] == True:
#         naam = request.json['naam']
#         data = aanwezig.query.filter_by(naam = naam).first()
#         print(data)
#         data.aanwezigheid=request.json['aanwezigheid']
#         db.session.commit()
#         return jsonify("Gelukt")
#     else:
#         return "Jij hebt geen recht"

if __name__ == '__main__':
    app.run(host="localhost", debug=True)
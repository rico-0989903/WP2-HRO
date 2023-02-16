import os
import sqlite3
import qrcode
from flask import Flask, render_template, jsonify, request, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import update


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__name__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'hro.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

app.app_context().push()

#Database models
class Student(db.Model):
    studentnummer = db.Column(db.Integer, primary_key=True, unique=True)
    naam = db.Column(db.String(150), nullable=False)
    klasinschrijvingen = db.relationship('KlasInschrijving', backref='klascode', lazy=True)
    lesinschrijving = db.relationship('LesInschrijving', backref='inschrijving', lazy=True)

class Docent(db.Model):
    docent_id = db.Column(db.Integer, primary_key=True, unique=True)
    naam = db.Column(db.String(150), nullable=False)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='inschrijving', lazy=True)

class Klas(db.Model):
    klascode = db.Column(db.String(150), primary_key=True, nullable=False)
    slc_docent = db.Column(db.String(150))
    klasinschrijvingen = db.relationship('KlasInschrijving', backref='studenten', lazy=True)

class Les(db.Model):
    les_id = db.Column(db.Integer, primary_key=True, nullable=False)
    vak = db.Column(db.String(150), nullable=False)
    datum = db.Column(db.DateTime, nullable=False)
    lesinschrijvingen = db.relationship('LesInschrijving', backref='inschrijving', lazy=True)

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

#Marshmellow schemas
class StudentSchema(ma.Schema):
    class Meta:
        fields = ('studentnummer', 'naam')

class DocentSchema(ma.Schema):
    class Meta:
        fields = ('docent_id', 'naam')

class KlasSchema(ma.Schema):
    class Meta:
        fields = ('klascode', 'slc_docent')

class LesSchema(ma.Schema):
    class Meta:
        fields = ('les_id', 'vak', 'datum')

class KlasInschrijvingSchema(ma.Schema):
    class Meta:
        fields = ('studentnummer', 'klascode')

class LesInschrijvingSchema(ma.Schema):
    class Meta:
        fields = ('id', 'studentnummer', 'docent_id', 'les_id', 'aannwezigheid_check', 'afwezigheid_rede')


@app.route("/")
def index():
    return render_template('home.html')

@app.route("/lessen")
def lessen():
    return render_template('lessen.html')

@app.route("/docenten")
def docenten():
    return render_template('docenten.html')

@app.route("/klassen")
def klassen():
    return render_template('klassen.html')

@app.route("/klas/<les>", methods = ['POST', 'GET'])
def klas(les):
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
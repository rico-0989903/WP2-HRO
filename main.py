import os
import sqlite3
import qrcode
from flask import Flask, render_template, jsonify, request, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import update


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__name__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class aanwezig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(30), unique=True, nullable=False)
    studentnummer = db.Column(db.Integer, unique=True, nullable=False)
    aanwezigheid = db.Column(db.String(8), nullable=False)

    def __init__(self, naam, studentnummer, aanwezigheid):
        self.naam = naam
        self.studentnummer = studentnummer
        self.aanwezigheid = aanwezigheid

class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'naam', 'studentnummer', 'aanwezigheid')

student_schema = ProductSchema()
students_schema = ProductSchema(many=True)

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
import os
import sqlite3
import qrcode
from flask import Flask, render_template, jsonify, request, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS


app = Flask(__name__)
# MarkO: This is required for clients running on different protocol/DNS/port numbers.
# I have a presentation on CORS if you need to know more.


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databases/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class aanwezig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(30), unique=True, nullable=False)
    studentnummer = db.Column(db.Integer, unique=True, nullable=False)

    def __repr__(self):
        return self.naam

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/lessen")
def lessen():
    return render_template('index.html')

@app.route("/docenten")
def docenten():
    return render_template('index.html')

@app.route("/klassen")
def klassen():
    
    return render_template('index.html',)

@app.route("/klas/<les>", methods = ['POST', 'GET'])
def klas(les):
    test = True
    img = qrcode.make(f"http://127.0.0.1:5000/{les}")
    img.save('static/qr.png')
    img = url_for('static', filename='qr.png')
    return render_template('qrcode.html', img=img, test=test, les=les)

@app.route("/les/<les>")
def aanwezigheid(les):
    return render_template('form.html', les=les)

@app.route("/test", methods = ['POST','GET'])
def test():
    
    data = [{"naam": "roman", "nummer": "1261"},
            {"naam": "roman2", "nummer": "1271"},
            {"naam": "roman3", "nummer": "1281"}
            ]
    #incomingdata = request.json
    #data.append(incomingdata)
    print(data)
    return jsonify(data)

@app.route("/data", methods = ['POST', 'GET'])
def data():
    
    data = aanwezig(naam=request.json['naam'], studentnummer=request.json['nummer'])

    db.session.add(data)
    db.session.commit()

    return {'id': aanwezig.id}
    

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import Session

app = Flask(__name__, static_url_path="/", static_folder="www")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scores.db"
db = SQLAlchemy(app)
CORS(app)


class Highscore(db.Model):
    # If no tablename is specified, the class name will be used as the table name
    # To keep this consistent with the example, I have to force this to "highscores"
    __tablename__ = "highscores"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer(), nullable=False)
    game = db.Column(db.String(120), nullable=False)

    # This function is not used ..yet
    @classmethod
    def get_highest(self):
        with Session(db.engine) as session:
            print(session.query(self.name, func.max(Highscore.score)).first())

    @staticmethod
    def get_games_list():
        games = db.session.execute(
            db.select(Highscore.game).distinct(Highscore.game).order_by(Highscore.game)
        ).all()
        # Here, games is a list of tuples, each tuple containing a single string
        # This is because we are selecting a single column
        unwrapped_games = [game[0] for game in games]
        return unwrapped_games


@app.route("/highscores/<game>", methods=["GET", "POST"])
def handle_highscores(game):
    if request.method == "POST":
        body = request.json
        try:
            score = Highscore(name=body["name"], score=body["score"], game=game)
            db.session.add(score)
            db.session.commit()
            result = "ok"
            error = ""
        except Exception as e:
            result = "error"
            error = str(e)
        return jsonify({"result": result, "error": error})
    elif request.method == "GET":
        # Here, scores is a list of rows, which have 1 Highscore object each
        scores = db.session.execute(
            db.select(Highscore)
            .filter_by(game=game)
            .order_by(Highscore.score.desc())
            .limit(10)
        ).all()

        result = []
        for row in scores:
            for score in row:
                result.append({"name": score.name, "score": score.score})

        scores_dict = {"game": game, "scores": result}
        return jsonify(scores_dict)


@app.route("/highscores")
def list_highscore_games():
    return jsonify({"games": Highscore.get_games_list()})


@app.route("/")
@app.route("/jquery")
def hello_jquery():
    return send_from_directory("www", "highscore_jquery.html")


@app.route("/javascript")
def hello_javascript():
    return send_from_directory("www", "highscore_js.html")


# Note that we need to push the create_all below the Highscores class
# definition because the class is used in the create_all function
app.app_context().push()
db.create_all()
app.run(debug=True, host="127.0.0.1", port=5002)

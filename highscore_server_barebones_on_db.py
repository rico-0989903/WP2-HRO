import os
import sqlite3

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import Datamodel as hs

app = Flask(__name__, static_url_path="/", static_folder="www")
# MarkO: This is required for clients running on different protocol/DNS/port numbers.
# I have a presentation on CORS if you need to know more.
CORS(app)




@app.route("/highscores/<game>", methods=["GET", "POST"])
def handle_highscores(game):
    if request.method == "POST":
        body = request.json
        try:
            highscores.insert_score(body["name"], body["score"], game)
            result = "ok"
            error = ""
        except hs.HighScores as e:
            result = "error"
            error = f"Missing required field ({e})"
        except Exception as e:
            result = "error"
            error = str(e)
        return jsonify({"result": result, "error": error})
    elif request.method == "GET":
        scores = highscores.get(game)
        scores_dict = {"game": game, "scores": scores}
        return jsonify(scores_dict)


@app.route("/highscores")
def list_highscore_games():
    return jsonify({"games": highscores.get_games_list()})


@app.route("/")
@app.route("/jquery")
def hello_jquery():
    return send_from_directory("www", "highscore_jquery.html")


@app.route("/javascript")
def hello_javascript():
    return send_from_directory("www", "highscore_js.html")


DATABASE_FILE = os.path.join(app.instance_path, "scores.db")
highscores = hs.HighScores(DATABASE_FILE)
app.run(debug=True, host="127.0.0.1", port=5001)

import requests
from requests_toolbelt.utils import dump


# I create my own exception type here so I can inform clients when we cannot reach the highscore server.
# This will probably be a common occurence.
class HighScoreException(Exception):
    pass


class HighScore:
    """
    This class functions as a client for communication with the Highscores server
    ...

    Attributes
    ----------
    game : str
        A game name that is used to identify the highscores, for example, "Tetris"
    server_url : str
        A full URL to the highscore server, for example, "http://127.0.0.1:5000"
        age of the person
    debug : boolean, optional
        If True, the client will print the HTTP request and response to the console

    Methods
    -------
    add_highscore(scorer, score):
        Sends the new highscore with the name of the scorer to the central server

    get_highscores():
        Retrieves the highscores for your game from the central server

    """
    def __init__(self, game, server_url="http://127.0.0.1:8080", debug=False):
        self.game = game
        self.server_url = server_url
        self.debug = debug

    def add_highscore(self, scorer, score):
        uri = "/highscores/" + self.game
        score = {"name": scorer, "score": int(score)}
        # Note that I pass the requests.post METHOD here, not a variable!
        json = self.__handle_request(requests.post, uri, json=score)
        if json["result"] != "ok":
            raise HighScoreException(f"Could not add highscore: {json['message']}")
        return json["result"]

    def get_highscores(self):
        uri = "/highscores/" + self.game
        # Note that I pass the requests.get METHOD here, not a variable!
        json = self.__handle_request(requests.get, uri)
        return json["scores"]

    def __handle_request(self, requests_function, uri, json=None):
        url = self.server_url + uri
        try:
            response_raw = requests_function(url=url, json=json)
        except requests.exceptions.ConnectionError:
            raise HighScoreException(f"Could not connect to HighScore server at {self.server_url}")
        if self.debug:
            print(dump.dump_all(response_raw).decode('utf-8'))
        return response_raw.json()

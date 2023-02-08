import random
import sys

from lib.highscore_client import HighScore

highscore_client = HighScore("lunarlander", server_url="http://127.0.0.1:5001")
score = random.randint(0, 100)
print(f"Hurray! {score}! You got a highscore!")
highscore_client.add_highscore("Mark", score)

highscores = highscore_client.get_highscores()
for highscore in highscores:
    print(highscore["name"] + ": " + str(highscore["score"]))

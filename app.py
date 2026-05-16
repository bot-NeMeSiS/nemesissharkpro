
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "NeMeSiS SHARK PRO V327 REAL FULL"

if __name__ == "__main__":
    app.run()

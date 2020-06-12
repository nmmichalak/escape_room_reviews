#!/usr/bin/python
import flask
import pandas as pd
import numpy as np

# create and configure the app
app = flask.Flask(__name__)
app.config.from_object(__name__)

# define functions, load data, etc.

# index html makes it pretty looking
@app.route("/", methods = ["GET"])
def index():
	return flask.render_template("index.html")

@app.route("/")
def results_table():
    return render_template("index.html", tables = pd.DataFrame(np.random.randn(20, 5)))

if __name__ == "__main__":
	app.run(host = "0.0.0.0", debug = False)
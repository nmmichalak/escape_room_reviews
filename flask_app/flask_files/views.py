# import modules
from flask import render_template
from flask_files import app

# two route decorators (@app.route()) create the mappings from urls "/" and "/index" to this function.
@app.route("/")
@app.route("/index")

# returns string message to be displayed on the user's web browser. 
def index():
    user = { 'nickname': 'Miguel' } # fake user
    return render_template("index.html", title = "Home", user = user)
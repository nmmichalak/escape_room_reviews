# packages
import flask

# create and configure the app
app = flask.Flask(__name__)
app.config.from_object(__name__)

# import views module
from next_escape import routes
# import packages
from flask import Flask
from flask_bootstrap import Bootstrap

# application object of class Flask
def create_app():
  app = Flask(__name__)
  Bootstrap(app)
  return app

# import modules
# views are the handlers that respond to requests from web browsers
# in flask views are written as python functions
# each view function is mapped to one or more request urls
from flask_files import views

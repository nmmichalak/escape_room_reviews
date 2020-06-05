# import packages
from flask import Flask

# application object of class Flask
app = Flask(__name__)

# import modules
# views are the handlers that respond to requests from web browsers
# in flask views are written as python functions
# each view function is mapped to one or more request urls
from flask_files import views

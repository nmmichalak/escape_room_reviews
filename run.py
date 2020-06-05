#!/usr/bin/env python
# /usr/bin/env will ensure the interpreter used is the first one on your environment's $PATH
# import app variable from flaskexample package
from flask_files import app

# invokes app module run method to start the server
# remember that the app variable holds the Flask instance, which is written in other files
app.run(debug = True)
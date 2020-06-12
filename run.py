#!/usr/bin/env python
from next_escape import app

# invokes app module run method to start the server
# remember that the app variable holds the Flask instance, which is written in other files
app.run(debug = True)
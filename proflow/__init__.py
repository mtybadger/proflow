"""Package initializer."""
import flask

app = flask.Flask(__name__)

# Read settings from config module
app.config.from_object('proflow.config')

import proflow.views

# Run a test server.
from flask import Flask

app = Flask(__name__)
app.config.from_object("config")

from flask_eventics.controllers import eventics

app.register_blueprint(eventics)
app.run(debug=True)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('public_config')
db = SQLAlchemy(app)

# TODO add logging and otherstuff

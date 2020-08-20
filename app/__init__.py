from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_rq2 import RQ
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
rq = RQ(app)
mongo = PyMongo(app)
bootstrap = Bootstrap(app)

from app import views, tasks
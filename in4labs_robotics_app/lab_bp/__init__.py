from flask import Blueprint

bp = Blueprint('lab', __name__)

from . import routes
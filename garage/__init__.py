from flask import Blueprint

garage = Blueprint('garage',__name__,template_folder='templates',url_prefix='/garage')

from .routes import *
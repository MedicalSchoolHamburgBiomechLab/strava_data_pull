from app import app, backend
from db import db

db.init_app(backend)


@backend.before_first_request
def create_tables():
    db.create_all()

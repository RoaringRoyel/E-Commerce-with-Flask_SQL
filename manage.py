from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from app import app, db  # Import your existing app and db

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()

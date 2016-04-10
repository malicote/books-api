import os

basedir = os.path.abspath(os.path.dirname(__file__))

# TODO: switch to postgres (sqlite can't handle concurrent access)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'books.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

DEFAULT_CATEGORIES = [
    "none",
    "paycheck",
    "bills",
    "grocery",
    "dining",
    "gas",
]

# TODO: get this working
APPLICATION_ROOT = "/books/api/v0.1"


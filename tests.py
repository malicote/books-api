#!flask/bin/python

import os
import datetime
import unittest

import sqlalchemy.exc as db_exceptions

from books_api import app, db
from books_api.models import Category, Account, Transaction
from public_config import basedir


def add_categories(categories):
    """
    Add categories to test database.
    Used to set up a test.
    :param categories: List of category descriptions to add.
    :return: None
    """
    for category in categories:
        db.session.add(Category(category=category))
    db.session.commit()


def db_add_all(items):
    for item in items:
        db.session.add(item)
    db.session.commit()


class ModelTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')

        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class CategoryModelTest(ModelTest):
    categories = [
        'dining',
        'income',
        'gas',
    ]

    def test_basic_category_addition(self):
        print("Testing basic category addition...")
        categories = self.__class__.categories
        add_categories(categories)

        saved_categories = [c.category for c in Category.query.all()]
        for category in categories:
            assert category in saved_categories

    def test_uniqueness(self):
        categories = self.__class__.categories
        add_categories(categories)

        duplicate_category = categories[0]
        db.session.add(Category(category=duplicate_category))
        try:
            db.session.commit()
            raise Exception("Failed to catch duplication of '{}' in Category entry.".format(duplicate_category))
        except db_exceptions.SQLAlchemyError as e:
            pass

    def test_is_category(self):
        print("Testing is_category...")
        categories = self.__class__.categories
        add_categories(categories)

        if Category.is_category('not_in_db'):
            raise Exception("is_category returned True for 'not_in_db'")

        if not Category.is_category(categories[0]):
            raise Exception("is_category returned False for '{}'".format(categories[0]))

    def test_add_category(self):
        print("Testing add_category...")
        Category.add_category('money')
        if not Category.is_category('money'):
            raise Exception("add_category failed to add 'money'")

    def test_get_all_categories(self):
        print("Testing get_all_categories...")
        categories = self.__class__.categories
        add_categories(categories)

        stored_categories = Category.get_all_categories()
        if categories.sort() != stored_categories.sort():
            print("stored_categories: {}".format(stored_categories))
            print("expected_categories: {}".format(categories))
            raise Exception("get_all_categories is missing categories.")

    def test_get_transactions(self):
        print("Testing get_transactions...")
        categories = self.__class__.categories
        add_categories(categories)

        account = Account.add_account('Wells Fargo', 'checking')
        account.add_transaction(
            description='Grocery_store #1',
            amount='100',
            date=datetime.date(2015, 12, 31),
            type='debit',
            category='grocery'
        )

        account.add_transaction(
            description='Grocery_story #2',
            amount='150',
            date=datetime.date(2016, 3, 30),
            type='credit',
            category='grocery'
        )

        grocery_category = Category(category='grocery')
        print grocery_category.get_transactions()



if __name__ == "__main__":
    unittest.main()

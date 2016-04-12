#!flask/bin/python

import os
import datetime
import unittest

import sqlalchemy.exc

from books_api import app, db
from books_api.models import Category, Account, Transaction, AccountException
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

def print_test_name(func):
    fname = func.func_name

    def run_test(*args, **kwargs):
        print "Running {}...".format(fname)
        return func(*args, **kwargs)

    return run_test

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

    @print_test_name
    def test_basic_category_addition(self):
        categories = self.__class__.categories
        add_categories(categories)

        saved_categories = [c.category for c in Category.query.all()]
        for category in categories:
            assert category in saved_categories

    @print_test_name
    def test_uniqueness(self):
        categories = self.__class__.categories
        add_categories(categories)

        duplicate_category = categories[0]
        db.session.add(Category(category=duplicate_category))
        try:
            db.session.commit()
            assert False, "Failed to catch duplication of '{}' in Category entry.".format(duplicate_category)
        except sqlalchemy.exc.IntegrityError as e:
            pass

    @print_test_name
    def test_is_category(self):
        categories = self.__class__.categories
        add_categories(categories)

        if Category.is_category('not_in_db'):
            assert False, "is_category returned True for 'not_in_db'"

        if not Category.is_category(categories[0]):
            assert False, "is_category returned False for '{}'".format(categories[0])

    @print_test_name
    def test_add_category(self):
        Category.add_category('money')
        if not Category.is_category('money'):
            assert False, "add_category failed to add 'money'"

    @print_test_name
    def test_get_all_categories(self):
        categories = self.__class__.categories
        add_categories(categories)

        stored_categories = Category.get_all_categories()
        if categories.sort() != stored_categories.sort():
            print("stored_categories: {}".format(stored_categories))
            print("expected_categories: {}".format(categories))
            assert False, "get_all_categories is missing categories."

    @print_test_name
    def test_get_transactions(self):
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

        account.add_transaction(
            description='Gas Station #1',
            amount='20',
            date=datetime.date(2015, 2, 10),
            type='credit',
            category='gas'
        )

        grocery_category = Category(category='grocery')
        assert len(grocery_category.get_transactions()) == 2, "Incorrect number of transactions"


class AccountModelTest(ModelTest):
    categories = [
        'dining',
        'income',
        'gas',
    ]

    """ Tests to write:
    - add account
        - reject existing account
    - get all accounts (list of account objects)
    - get account object by name
    - add new transaction
        - test that it does not accept invalid input?y
        - test that it must be a valid account
    - get transactions
        - filtering testing?
    - test that it updates the total correctly
    """

    @print_test_name
    def test_add_account(self):
        acct_name = "Wells Fargo"
        acct_type = "Checking"

        added_account = Account.add_account(description=acct_name, type=acct_type)
        assert added_account is not None

        acct = Account.query.filter_by(description=acct_name).first()

        assert acct.description == acct_name and acct.type == acct_type.lower()

        try:
            added_account = Account.add_account(description=acct_name, type=acct_type)
            assert False, "Added account that already existed?"
        except AccountException as e:
            pass

    @print_test_name
    def test_get_all_accounts(self):
        Account.add_account("Account1", "checking")
        Account.add_account("Account2", "credit card")
        Account.add_account("Account3", "savings")

        accounts = Account.get_all()

        assert len(accounts) == 3, "Did not list all available accounts"

    @print_test_name
    def test_get_by_name(self):
        Account.add_account("Account1", "checking")
        Account.add_account("Account2", "credit card")
        Account.add_account("Account3", "savings")

        account_1 = Account.get_by_name("Account1")

        assert account_1.description == "Account1" and account_1.type == "checking",\
            "Did not retrive account as expected: {}".format(account_1)

        account_2 = Account.get_by_name("Account2")

        assert account_2.description == "Account2" and account_2.type == "credit card", \
            "Did not retrive account as expected: {}".format(account_2)

        unknown = Account.get_by_name("unknown")
        assert unknown is None, "Retrieved unknown account: {}".format(unknown)

    @print_test_name
    def test_get_by_id(self):
        a1 = Account.add_account("Account1", "checking")
        a2 = Account.add_account("Account2", "credit card")
        a3 = Account.add_account("Account3", "savings")

        account_1 = Account.get_by_id(a1.id)

        assert (a1.description == account_1.description
                and a1.type == account_1.type
                and a1.id == account_1.id), "Failed to retrieve account2 by id"

        account_2 = Account.get_by_id(a2.id)

        assert (a2.description == account_2.description
                and a2.type == account_2.type
                and a2.id == account_2.id), "Failed to retrieve account2 by id"

        unknown = Account.get_by_id(4)
        assert unknown is None, "Retrieved unknown account by id: {}".format(unknown)

    @print_test_name
    def test_basic_add_transaction(self):
        account1 = Account.add_account("Account1", "checking")
        account2 = Account.add_account("Account2", "savings")

        # Only need one category
        test_category = "test"
        Category.add_category(test_category)

        """
            def add_transaction(self, date, description, amount, type, category):

        """
        # TODO: test duplicate transactions
        transactions1 = [
            (datetime.date(2015, 1, 1), "place #1", 100, "debit", test_category),
            (datetime.date(2016, 2, 3), "place #2", 10, "credit", test_category),
            (datetime.date(2015, 1, 1), "place #3", 100, "debit", test_category),
            (datetime.date(2016, 2, 3), "place #4", 10, "credit", test_category),
            (datetime.date(2015, 3, 1), "place #5", 100, "debit", test_category),
            (datetime.date(2016, 4, 3), "place #6", 10, "credit", test_category),
            (datetime.date(2015, 5, 1), "place #7", 101, "debit", test_category),
            (datetime.date(2016, 7, 3), "place #9", 11, "credit", test_category),
            (datetime.date(2015, 8, 1), "place #10", 111, "debit", test_category),
            (datetime.date(2016, 9, 3), "place #11", 15, "credit", test_category),
            (datetime.date(2016, 10, 3), "place #12", 20, "credit", test_category),
            (datetime.date(2016, 11, 3), "place #13", 25, "credit", test_category),
            (datetime.date(2016, 11, 4), "place #14", 30, "credit", test_category),
        ]

        transactions2 = [
            (datetime.date(2015, 3, 1), "place #3", 30, "debit", test_category),
            (datetime.date(2016, 4, 3), "place #4", 20, "credit", test_category),
        ]

        for tx in transactions1:
            account1.add_transaction(*tx)

        for tx in transactions2:
            account2.add_transaction(*tx)

        assert len(account1.get_transactions()) == len(transactions1), "Failed to add transactions to account1"
        assert len(account2.get_transactions()) == len(transactions2), "Failed to add transactions to account2"

    @print_test_name
    def test_add_transaction_with_balance(self):
        account1 = Account.add_account("Account1", "checking")
        account2 = Account.add_account("Account2", "savings")

        # Only need one category
        test_category = "test"
        Category.add_category(test_category)

        # TODO: test duplicate transactions
        transactions1 = [
            (datetime.date(2015, 1, 1), "place #1", 100, "debit", test_category),
            (datetime.date(2016, 2, 3), "place #2", 10, "credit", test_category),
            (datetime.date(2015, 1, 1), "place #3", 100, "debit", test_category),
        ]
        a1_exp_balance = -100 + 10 - 100

        transactions2 = [
            (datetime.date(2015, 3, 1), "place #3", 30, "debit", test_category),
            (datetime.date(2016, 4, 3), "place #4", 20, "credit", test_category),
        ]
        a2_exp_balance = -30 + 20


        for tx in transactions1:
            account1.add_transaction(*tx)

        for tx in transactions2:
            account2.add_transaction(*tx)

        a1 = Account.get_by_id(account1.id)
        a2 = Account.get_by_id(account2.id)

        assert a1.balance == a1_exp_balance and a2.balance == a2_exp_balance, "Balances not updated correctly."

    @print_test_name
    def test_rollback_transaction(self):
        account1 = Account.add_account("Account1", "checking")
        account2 = Account.add_account("Account2", "savings")

        # Only need one category
        test_category = "test"
        Category.add_category(test_category)

        # TODO: test duplicate transactions
        transactions1 = [
            (datetime.date(2015, 1, 1), "place #1", 100, "debit", test_category),
            (datetime.date(2016, 2, 3), "place #2", 10, "credit", test_category),
            (datetime.date(2015, 1, 1), "place #3", 100, "debit", test_category),
        ]
        a1_exp_balance = -100 + 10 - 100

        transactions2 = [
            (datetime.date(2015, 3, 1), "place #3", 30, "debit", test_category),
            (datetime.date(2016, 4, 3), "place #4", 20, "credit", test_category),
        ]
        a2_exp_balance = -30 + 20

        added_tx1 = []
        for tx in transactions1:
            added_tx1.append(account1.add_transaction(*tx))

        added_tx2 = []
        for tx in transactions2:
            added_tx2.append(account2.add_transaction(*tx))

        a1 = Account.get_by_id(account1.id)
        a2 = Account.get_by_id(account2.id)

        assert a1.balance == a1_exp_balance and a2.balance == a2_exp_balance, "Balances not updated correctly."

        account1.remove_transaction(added_tx1[0])
        assert account1.balance == a1_exp_balance + 100 and account2.balance == a2_exp_balance,\
            "Rollback balance not calculated correctly"

        account1.remove_transaction(added_tx1[1])
        assert account1.balance == a1_exp_balance + 100 - 10 and account2.balance == a2_exp_balance, \
            "Rollback balance w/ credit not calculated correctly"

        try:
            account1.remove_transaction(added_tx2[0])
            assert False, "Removed transaction that wasn't part of the account"
        except AccountException as e:
            pass

        try:
            account1.remove_transaction(added_tx1[0])
            assert False, "Removed transaction that was already removed."
        except AccountException as e:
            pass


if __name__ == "__main__":
    unittest.main()

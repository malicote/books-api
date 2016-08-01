#!flask/bin/python

import sys
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

def db_add_accounts(desc_type_pairs):
    accts = []
    for desc, type in desc_type_pairs:
        acct = Account(description=desc, type=type)
        accts.append(acct)

    db_add_all(accts)

    return accts

def db_add_transactions(account, transaction_tuples):
    # [(datetime.date(2015, 1, 1), "place #1", 100, "debit", test_category), ...]
    tx_list = []
    for tx in transaction_tuples:
        transaction = account.add_transaction(*tx)
        tx_list.append(transaction)
        db.session.add(transaction)

    db.session.add(account)
    db.session.commit()

    return tx_list


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

        account, = db_add_accounts([('Wells Fargo', 'checking')])
        transactions2 = [
            account.add_transaction(datetime.date(2015, 3, 1), "place #3", 30, "debit", 'grocery'),
            account.add_transaction(datetime.date(2016, 4, 3), "place #4", 20, "credit", 'grocery'),
            account.add_transaction(datetime.date(2016, 3, 3), "place #5", 21, "credit", 'gas'),
        ]

        db.session.add(account)
        for tx in transactions2:
            db.session.add(tx)

        db.session.commit()

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

        db.session.add(Account(description=acct_name, type=acct_type))
        db.session.commit()

        acct = Account.query.filter_by(description=acct_name).first()

        print acct_name
        print acct_type
        print acct

        assert acct.description == acct_name and acct.type == acct_type.lower()

        try:
            db.session.add(Account(description=acct_name, type=acct_type))
            db.session.commit()
            assert False, "Added account that already existed?"
        except sqlalchemy.exc.IntegrityError as e:
            pass

    @print_test_name
    def test_get_all_accounts(self):
        db.session.add(Account(description="Account1", type="checking"))
        db.session.add(Account(description="Account2", type="credit card"))
        db.session.add(Account(description="Account3", type="savings"))
        db.session.commit()

        accounts = Account.get_all()

        assert len(accounts) == 3, "Did not list all available accounts"


    @print_test_name
    def test_get_by_name(self):
        db_add_accounts([
            ("Account1", "checking"),
            ("Account2", "credit card"),
            ("Account3", "savings"),
        ])

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
        a1, a2, a3 = db_add_accounts([
            ("Account1", "checking"),
            ("Account2", "credit card"),
            ("Account3", "savings"),
        ])

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
        account1, account2 = db_add_accounts([
            ("Account1", "checking"),
            ("Account2", "savings"),
        ])

        # Only need one category
        test_category = "test"
        add_categories([test_category])

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

        db_add_transactions(account1, transactions1)
        db_add_transactions(account2, transactions2)

        assert len(account1.get_transactions()) == len(transactions1), "Failed to add transactions to account1"
        assert len(account2.get_transactions()) == len(transactions2), "Failed to add transactions to account2"

    @print_test_name
    def test_add_transaction_with_balance(self):
        account1, account2 = db_add_accounts([
            ("Account1", "checking"),
            ("Account2", "savings"),
        ])

        # Only need one category
        test_category = "test"
        add_categories([test_category])

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
        account1, account2 = db_add_accounts([
            ("Account1", "checking"),
            ("Account2", "savings"),
        ])

        # Only need one category
        test_category = "test"
        add_categories([test_category])

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

        added_tx1 = db_add_transactions(account1, transactions1)
        added_tx2 = db_add_transactions(account2, transactions2)

        a1 = Account.get_by_id(account1.id)
        a2 = Account.get_by_id(account2.id)

        assert a1.balance == a1_exp_balance and a2.balance == a2_exp_balance, "Balances not updated correctly."

        removed_transaction = account1.remove_transaction(added_tx1[0])
        db.session.add(account1)
        db.session.delete(removed_transaction)
        db.session.commit()

        db.session.refresh(account1)
        assert account1.balance == a1_exp_balance + 100 and account2.balance == a2_exp_balance,\
            "Rollback balance not calculated correctly"

        removed_transaction = account1.remove_transaction(added_tx1[1])
        db.session.add(account1)
        db.session.delete(removed_transaction)
        db.session.commit()

        db.session.refresh(account1)
        assert account1.balance == a1_exp_balance + 100 - 10 and account2.balance == a2_exp_balance, \
            "Rollback balance w/ credit not calculated correctly"

        try:
            _ = account1.remove_transaction(added_tx2[0])
            assert False, "Removed transaction that wasn't part of the account"
        except AccountException as e:
            pass

        try:
            _ = account1.remove_transaction(added_tx1[0])
            assert False, "Removed transaction that was already removed."
        except AccountException as e:
            pass


if __name__ == "__main__":
    unittest.main()

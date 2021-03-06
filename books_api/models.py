import sys

import sqlalchemy.exc

from books_api import db
from books_api import app

# TODO: what is the best way to model this instead of strings?

# TODO: split out some of this logic?

account_types = [
    "credit card",
    "checking",
    "savings"
]

transaction_types = [
    "debit",
    "credit"
]

# TODO: better exception handling capabilities


class GenericBooksException(Exception):
    pass


class CategoryException(GenericBooksException):
    pass


class CategoryNotFoundException(CategoryException):
    pass


class AccountException(GenericBooksException):
    pass


class TransactionException(GenericBooksException):
    pass


# todo: determine how to get categories
# todo: possible allow no categoies (none)
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), unique=True, nullable=False, index=True)
    transactions = db.relationship('Transaction', backref='category_info', lazy='dynamic')

    def __repr__(self):
        return "<Category {}: '{}'>".format(self.id, self.category)

    @staticmethod
    def is_category(category):
        # TODO: test if this can be injected
        return Category.query.filter_by(category=category).first() is not None

    @staticmethod
    def get_all_categories():
        """
        :return: All categories as list of strings
        """
        return [c.category for c in Category.query.all()]

    @staticmethod
    def get_category(description):
        if not Category.is_category(description):
            return None

        return Category(category=description)

    def get_transactions(self, number_of_results=10):
        # TODO: allow options here
        return Transaction.query\
            .filter_by(category=self.category)\
            .order_by(Transaction.date.desc())\
            .limit(number_of_results)\
            .all()


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64), index=True, nullable=False, unique=True)
    # In cents, TODO: use a different type.
    balance = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(64), nullable=False)

    transactions = db.relationship('Transaction', backref='account_info', lazy='dynamic')

    def __init__(self, **kwargs):
        description = kwargs.get('description', '')
        type = kwargs.get('type', '')
        if not description or not type:
            print("add_account error: empty description or '{}' not in '{}'".format(type, account_types))
            raise AccountException("Missing description or account type.")

        # Save type as lower case only
        kwargs['type'] = kwargs['type'].lower()

        if 'balance' not in kwargs:
            kwargs['balance'] = 0

        super(Account, self).__init__(**kwargs)

    @staticmethod
    def get_all():
        return Account.query.all()

    @staticmethod
    def get_by_name(name):
        # TODO: what if it doesn't exist?  Return None or throw exception?
        return Account.query.filter_by(description=name).first()

    @staticmethod
    def get_by_id(id):
        return Account.query.get(id)

    def as_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "balance": self.balance,
            "type": self.type,
        }

    def __update_balance_by(self, amount, transaction_type):
        # TODO ensure this is OK
        self.balance = self.balance + amount if transaction_type == "credit"\
            else self.balance - amount

    def add_transaction(self, date, description, amount, type, category):
        # TODO: how to ensure date is a datetime object, or ensure it can be?
        # TODO: determine if amount isn't int
        # Caller is required to call the returned object and the self object
        """
        :param date: Datetime object
        :param description: Description of transaction
        :param amount: amount of transaction in cents
        :param type: Type of transaction
        :param category: Transaction category
        :return: Transaction added
        """
        amount = int(amount)
        new_transaction = Transaction(
            account_id=self.id,
            description=description,
            amount=amount,
            type=type,
            date=date,
            category=category
        )

        self.__update_balance_by(amount, type)

        return new_transaction

    def get_transactions(self):
        # TODO: allow filtering options here
        return Transaction.query \
            .filter_by(account_id=self.id) \
            .order_by(Transaction.date.desc()) \
            .all()

    def remove_transaction(self, transaction):
        """
        Roll back transaction for this account.
        Caller is required to add account & remove transaction database session
        :param transaction: Valid transaction object w/ id.
        :return: Raise Exception if id isn't found for this account.
        """
        # Check that transaction still exists.
        record_list = Transaction.get_transactions(transaction_id=transaction.id)
        if not record_list:
            raise AccountException("Transaction does not exist.")

        record = record_list.pop()

        # TODO: how to guarantee that transaction is the correct object
        if record.account_id != self.id:
            raise AccountException("Transaction {} not found for this account {}".format(
                record, self
            ))

        self.__update_balance_by(-record.amount, record.type)

        return record

    def __repr__(self):
        return "<Account id: {}, description: '{}', balance: {}, type: {} >".format(
            self.id, self.description, self.balance, self.type
        )


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

    description = db.Column(db.String(64), index=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(64), nullable=False)

    category = db.Column(db.String(64), db.ForeignKey('category.category'))
    date = db.Column(db.Date, nullable=False)

    @staticmethod
    def get_transactions(transaction_id=None,
                         account_id=None, description=None,
                         amount=None, date=None, type=None, category=None):
        # TODO: clean this mess up
        t = Transaction.query
        if transaction_id:
            t = t.filter_by(id=transaction_id)
        if account_id:
            t = t.filter_by(account_id=account_id)
        if description:
            t = t.filter_by(description=description)
        if date:
            t = t.filter_by(date=date)
        if type:
            t = t.filter_by(type=type)
        if amount:
            t = t.filter_by(amount=amount)
        if category:
            t = t.filter_by(category=category)

        return t.order_by(Transaction.date.desc()).all()

    def as_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'description': self.description,
            'amount': self.amount,
            'type': self.type,
            'category': self.category,
            'date': str(self.date),
        }

    def __repr__(self):
        return "<Transaction id: {}, account_id: {}, description: '{}'," \
               "amount: {}, type: {}, category: {}, date: {} >".format(
            self.id,
            self.account_id,
            self.description,
            self.amount,
            self.type,
            self.category,
            self.date
        )

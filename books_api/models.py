import sys

from books_api import db
from books_api import app

account_types = [
    "credit card",
    "checking",
    "savings"
]

transaction_types = [
    "debit",
    "credit"
]


# todo: determine how to get categories
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), unique=True)
    transactions = db.relationship('Transaction', backref='category_info', lazy='dynamic')

    def __repr__(self):
        return "<Category {}: '{}'>".format(self.id, self.category)

    @staticmethod
    def is_category(category):
        # TODO: test if this can be injected
        return Category.query.filter_by(category=category).first() is not None

    @staticmethod
    def add_category(category_description):
        if not Category.is_category(category_description):
            db.session.add(Category(category=category_description))
            # Add logic handling here.
            db.session.commit()

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

    @staticmethod
    def add_account(description, type):
        if not description or type not in account_types:
            # TODO raise exception
            return None

        new_account = Account(description=description, balance=0, type=type)
        db.session.add(new_account)
        db.session.commit()
        return new_account

    @staticmethod
    def get_all():
        return Account.query.all()

    @staticmethod
    def get_by_name(name):
        return Account.query.filter_by(description=name).first()

    def add_transaction(self, date, description, amount, type, category):
        new_transaction = Transaction(
            account_id=self.id,
            description=description,
            amount=amount,
            type=type,
            date=date,
            category=category
        )

        db.session.add(new_transaction)
        db.session.commit()

    def get_transactions(self, number_of_results=10):
        # TODO: allow options here
        return Transaction.query \
            .filter_by(account_id=self.id) \
            .order_by(Transaction.date.desc()) \
            .limit(number_of_results) \
            .all()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

    description = db.Column(db.String(64), index=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(64), nullable=False)

    category = db.Column(db.String(64), db.ForeignKey('category.category'))
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return "<Transaction id: {}, account_id: {}, description: '{}'," \
               "amount: {}, type: {}, category: {}, date:{}".format(
            self.id,
            self.account_id,
            self.description,
            self.amount,
            self.type,
            self.category,
            self.date
        )

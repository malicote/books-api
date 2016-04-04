import sys

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

class GenericAccountingException(Exception):
    pass


class CategoryException(GenericAccountingException):
    pass


class CategoryNotFoundException(CategoryException):
    pass


class AccountException(GenericAccountingException):
    pass


class TransactionException(GenericAccountingException):
    pass


# todo: determine how to get categories
# todo: possible allow no categoies (none)
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
        type = type.lower()
        if not description or type not in account_types:
            print("Error: empty description or '{}' not in '{}'".format(type, account_types))
            # TODO how to add account types?
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
        # TODO: what if it doesn't exist?  Return None or throw exception?
        return Account.query.filter_by(description=name).first()

    @staticmethod
    def get_by_id(id):
        return Account.query.filter_by(id=id).first()

    def __update_balance_by(self, amount, transaction_type):
        # TODO ensure this is OK
        self.balance = self.balance + amount if transaction_type == "credit"\
            else self.balance - amount

        db.session.commit()

    def add_transaction(self, date, description, amount, type, category):
        # TODO: how to ensure data is a datetime object, or ensure it can be?
        """
        :param date: Datetime object
        :param description: Description of transaction
        :param amount: amount of transaction in cents
        :param type: Type of transaction
        :param category: Transaction category
        :return: Transaction added
        """
        amount = int(amount)
        new_transaction = Transaction.add_transaction(
            account_id=self.id,
            description=description,
            amount=amount,
            type=type,
            date=date,
            category=category
        )

        self.__update_balance_by(amount, type)

        # TODO-ASAP: catch exception & roll back if needed
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

        # Todo: catch exception
        record.remove()

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
    def add_transaction(account_id, description, date, amount, type, category):
        new_transaction = Transaction(
            account_id=account_id,
            description=description,
            amount=amount,
            type=type,
            date=date,
            category=category
        )

        db.session.add(new_transaction)
        db.session.commit()
        # TODO: catch exception
        return new_transaction

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

    def remove(self):
        db.session.delete(self)
        db.session.commit()


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

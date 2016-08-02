#!/usr/bin/python

import sys
import requests
import json
import datetime

base_url = "http://localhost:5000"


class BooksAPIException(Exception):
    pass


""" TODO:
    - Handle lack of JSON in response.
"""



class Book(object):
    """ Actions:
        - connect to specific book
        - get accounts in book
        - list categories in book
        - add an account
        - remove an account
        - get transaction summary
    """
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __url(self, *args):
        """
        Translates uri into url
        :param uri: /<uri> of the endpoint
        :return: base + uri
        """
        return self.endpoint + "/".join(args)

    def get_accounts(self):
        r = requests.get(self.__url('/accounts'))
        resp = r.json()

        if r.status_code != 200:
            raise BooksAPIException("Failure [{}]: {}".format(
                r.status_code, resp
            ))

        # TODO: what if 'accounts' not in resp?

        return resp['accounts']

    def add_account(self, description, type, initial_balance=0):
        new_account = {
            "description": description,
            "type": type,
            "balance": initial_balance,
        }

        r = requests.put(self.__url("/accounts"), json=new_account)

        if r.status_code != 200:
            raise BooksAPIException("Failed to add account {} [{}]: {}".format(
                description, r.status_code, r.json())
            )

    @staticmethod
    def acct_to_str(account):
        return "Account {} -- Desc: '{}' ({}) -- Balance: {}".format(
            account['id'],
            account['description'],
            account['type'],
            account['balance'],
        )

    def add_transaction_to_account(self, account, transaction):
        """
        :param account: account dict, must contain info returned
        from get_account
        :param transaction: transaction dict.  must contain:
            date - date of transaction
            description
            amount - in cents
            type - credit or debit
            category
        :return:
            Throws BooksAPIException on error
        """
        tx_fields = ['date', 'description', 'amount', 'type', 'category']

        try:
            request_body = {}

            for field in tx_fields:
                request_body[field] = transaction[field]

        except KeyError as e:
            raise BooksAPIException("Transaction missing info: {}".format(e))


        uri = self.__url(account['uri'], 'transactions')
        r = requests.put(uri, json=request_body)
        if r.status_code != 200:
            raise BooksAPIException("Failed to transaction '{}' to account {} [{}]: {}".format(
                request_body['description'], account['description'], r.status_code, r.json())
            )

        return r.json()['transaction']

    def get_transactions_for_account(self, account):
        uri = self.__url(account['uri'], 'transactions')
        r = requests.get(uri)
        if r.status_code != 200:
            raise BooksAPIException("Failed to get transactions for account {} [{}]: {}".format(
                account['description'], r.status_code, r.json())
            )

        resp = r.json()

        return resp['transactions']



    def get_categories(self):
        r = requests.get(self.__url('/categories'))
        resp = r.json()

        if r.status_code != 200:
            raise BooksAPIException("Failure [{}]: {}".format(
                r.status_code, resp
            ))


        return resp['categories']



def get_accounts():
    r = requests.get(base_url + "/accounts")
    return r.json()


def get_account(id):
    r = requests.get(base_url + "/accounts/" + str(id))
    return r.json()


def add_account(description, type):
    new_account = {
        "description": description,
        "type": type
    }

    r = requests.put(base_url + "/accounts", json=new_account)

    return r.status_code, r.json()


def get_categories():
    r = requests.get(base_url + "/categories")
    return r.status_code, r.json()


def add_categories(categories):
    new_categories = {
        "categories": [c for c in categories]
    }

    r = requests.put(base_url + "/categories", json=new_categories)
    return r.status_code, r.json()


def main():
    books_api = Book(base_url)
    print "\n".join([str(a) for a in books_api.get_accounts()])
    print books_api.get_categories()

    accounts = books_api.get_accounts()
    acct1 = accounts[0]

    transaction = {
        "date": str(datetime.datetime.strftime(datetime.datetime.now(),
                                               "%d/%m/%Y %H:%M:%S")),
        "description": "gasoline",
        "amount": 1065,
        "type": 'debit',
        "category": 'gasoline',
    }

    print books_api.add_transaction_to_account(acct1, transaction)

    print "\n".format([t for t in books_api.get_transactions_for_account(acct1)])
    print "\n".join([str(a) for a in books_api.get_accounts()])
    sys.exit(0)

if __name__ == "__main__":
    main()

    print("Listing all accounts:")
    accounts = get_accounts()
    print(json.dumps(accounts, indent=4))

    print("Adding WF/checking account...")
    code, response = add_account("WF", "checking")
    print("Response: ({}), {}".format(code, json.dumps(response, indent=4)))

    code, response = add_account("BOA", "checking")
    print("Response: ({}), {}".format(code, json.dumps(response, indent=4)))

    print("Response: {}".format(json.dumps(accounts, indent=4)))

    for account in accounts['accounts']:
        print("Account {}:\n{}".format(account['id'], json.dumps(get_account(account['id']), indent=4)))

    print("Account #100:\n{}".format(json.dumps(get_account(100), indent=4)))

    code, categories = get_categories()
    print("Categories ({}): {}".format(code, json.dumps(categories, indent=4)))

    new_categories_1 = ["dining", "bills"]
    new_categories_2 = ["rent", "grocery"]

    code, response = add_categories(new_categories_1)
    print("Response after adding categories ({}): {}".format(code, json.dumps(response, indent=4)))

    code, categories = get_categories()
    print("Reading back categories ({}): {}".format(code, json.dumps(categories, indent=4)))


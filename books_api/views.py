#!flask/bin/python

import time
import datetime

from flask import Flask, jsonify, request, url_for, make_response, abort

from books_api import app, db
from .models import Category, Account, Transaction
from .models import GenericBooksException, AccountException, CategoryException

# TODO: auth


def add_public_uri_to_account(account_dict):
    account_dict['uri'] = url_for('get_account', id=account_dict['id'])
    return account_dict


@app.route("/categories", methods=['GET'])
def get_categories():
    return jsonify({
        'categories': Category.get_all_categories()
    })

@app.route('/categories', methods=['PUT'])
def add_categories():
    """
    Expects format:
    {
        "categories": [
            "new_category1",
            "new_category2",
            ...
        ]
    """
    if not request.json or "categories" not in request.json:
        abort(400, "New categories must contain list of categories.")

    new_categories = request.json.get('categories')
    try:
        Category.add_categories(new_categories)
    except CategoryException as e:
        print("add_categories error: {}".format(e))
        abort(500, "Internal error")

    return jsonify({
        'categories': new_categories
    })


@app.route("/accounts", methods=['GET'])
def get_accounts():
    description = request.args.get('description')

    if description:
        account = Account.get_by_name(description)
        accounts = [account.as_dict()] if account else []
    else:
        accounts = [acct.as_dict() for acct in Account.get_all()]

    return jsonify({
       "accounts": map(add_public_uri_to_account, accounts)
    })


@app.route("/accounts/<int:id>", methods=['GET'])
def get_account(id):
    account = Account.get_by_id(id)

    if account:
        return jsonify({
            "account": add_public_uri_to_account(account.as_dict())
        })
    else:
        abort(404, "Account does not exist.")


@app.route("/accounts/<int:id>/summary", methods=['GET'])
def get_account_summary(id):
    abort(404, "Not implemented.")


@app.route("/accounts/<int:id>/transactions", methods=['GET'])
def get_account_transactions(id):
    account = Account.get_by_id(id)
    if not account:
        abort(404, "Account does not exist.")

    transactions = account.get_transactions()
    return jsonify({
        "transactions": [transaction.as_dict() for transaction in transactions]
    })


@app.route("/accounts", methods=['PUT'])
def add_account():
    if not request.json:
        abort(400, "Invalid request format.")

    if 'description' not in request.json or 'type' not in request.json:
        abort(400, "New account must contain description and type")

    # TODO: handle bad input
    try:
        new_account = Account.add_account(request.json['description'],
                                          request.json['type'])
    except AccountException as e:
        abort(409, "Account already exists")
    except GenericBooksException as e:
        abort(500, "Internal error")

    print("Added new account: {}".format(new_account))
    return jsonify(new_account.as_dict())



@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request',
                                  'message': error.description}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Resource not found',
                                  'message': error.description}), 404)

@app.errorhandler(409)
def not_found(error):
    return make_response(jsonify({'error': 'Resource already exists',
                                  'message': error.description}), 409)

@app.errorhandler(500)
def not_found(error):
    return make_response(jsonify({'error': 'An internal error occurred.',
                                  'message': error.description}), 500)

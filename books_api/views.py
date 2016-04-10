#!flask/bin/python

import time
import datetime

from flask import Flask, jsonify, request, url_for, make_response, abort

from books_api import app, db
from .models import Category, Account, Transaction

# TODO: auth


@app.route("/accounts", methods=['GET'])
def get_accounts():
    accounts = [acct.as_dict() for acct in Account.get_all()]

    return jsonify({
        "accounts": accounts
    })


@app.route("/accounts/<int:id>", methods=['GET'])
def get_account(id):
    account = Account.get_by_id(id)

    if account:
        return jsonify({
            "account": account.as_dict()
        })
    else:
        abort(404, "Account does not exist.")


@app.route("/accounts", methods=['PUT'])
def add_account():
    if not request.json:
        abort(400, "Invalid request format.")

    if 'description' not in request.json or 'type' not in request.json:
        abort(400, "New account must contain description and type")

    # TODO: handle bad input
    new_account = Account.add_account(request.json['description'], request.json['type'])
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


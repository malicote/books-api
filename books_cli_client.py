#!/usr/bin/python

import requests
import json

base_url = "http://localhost:5000"

# TODO: develop proper client

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


if __name__ == "__main__":
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

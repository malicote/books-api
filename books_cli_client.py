#!/usr/bin/python

import requests
import json

base_url = "http://localhost:5000"


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


if __name__ == "__main__":
    print("Listing all accounts:")
    print(json.dumps(get_accounts(), indent=4))

    #print("Adding WF/checking account...")
    #code, response = add_account("WF", "checking")
    #print("Response: ({}), {}".format(code, json.dumps(response, indent=4)))
    print("Account #1:\n{}".format(json.dumps(get_account(1), indent=4)))
    print("Account #100:\n{}".format(json.dumps(get_account(100), indent=4)))

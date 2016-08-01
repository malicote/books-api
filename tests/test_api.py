#!flask/env/python

import os
import datetime
import unittest

import boots_api_client

class APITest(unittest.TestCase):
    def setUp(self):
        print "Setting up"

    def tearDown(self):
        print "Tearing down"

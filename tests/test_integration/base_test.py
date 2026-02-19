import unittest
from app import create_app, db


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True

        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        self.connection = db.engine.connect()
        self.transaction = self.connection.begin()

        db.session.bind = self.connection
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        self.transaction.rollback()
        self.connection.close()
        db.session.remove()
        self.app_context.pop()

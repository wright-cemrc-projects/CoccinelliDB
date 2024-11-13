# import unittest
# from app import create_app, db
# from app.models import FacilityModel
# from config import TestingConfig

# class BasicTestCase(unittest.TestCase):

#     def setUp(self):
#         # Set up the app in testing mode
#         self.app = create_app(config_class=TestingConfig)
#         self.app_context = self.app.app_context()
#         self.app_context.push()
#         db.create_all()

#         # Set up the test client
#         self.client = self.app.test_client()

#     def tearDown(self):
#         # Remove the session and drop all tables
#         db.session.remove()
#         db.drop_all()
#         self.app_context.pop()

#     def test_index(self):
#         # Test the index route
#         response = self.client.get('/')
#         self.assertEqual(response.status_code, 200)
#         self.assertIn(b'Hello, World!', response.data)

# if __name__ == '__main__':
#     unittest.main()

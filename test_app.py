import os
import unittest
from flask import Flask, url_for, render_template, redirect, request
from app import app

class TestApp(unittest.TestCase):
    
    def test_index(self):
        the_test = app.test_client(self)
        response = the_test.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_content_get_books(self):
        the_test = app.test_client(self)
        response = the_test.get('/')
        self.assertIn(b'Looking for a book?', response.data)
        
if __name__ == '__main__':
    unittest.main()

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
    
    def test_notfound_get_books(self):
        the_test = app.test_client(self)
        book_notfound_name="qWertY29"
        book_url="/book/"+ book_notfound_name
        response = the_test.get(book_url)
        self.assertIn(b'You should be redirected automatically to target URL: <a href="/book_not_found">', response.data)

    def test_found_get_books(self):
        the_test = app.test_client(self)
        book_found_name="Christmas Carol"
        book_url="/book/"+ book_found_name
        response = the_test.get(book_url)
        self.assertIn(b'Charles Dickens', response.data)    
if __name__ == '__main__':
    unittest.main()

import os
import unittest
from flask import Flask, url_for, render_template, redirect, request
from flask_pymongo import PyMongo
from app import app
class TestApp(unittest.TestCase):
    
    ########################
    #### class variables ###
    ########################
    
    mongo=PyMongo(app)
    books=mongo.db.books
    
    #test book
    title="test title"
    author="test author"
    genre="test genre"
    description="test description that ends here. And, then, goes on."
    rating=[]
    test_book={
                "book_title":title,
                "book_author":author,
                "book_genre": genre,
                "book_description":description,
                "book_rating":rating
                }
    
    ########################
    #### helper methods ####
    ########################
    
    # server response to specific url request
    def server_response(self, page):
        return self.the_test.get(page)
    
    # inserts a test book in Mongo DB
    def insert_test_book(self, book):
        TestApp.books.insert_one(book)
    
    def remove_test_book(self, book):
        TestApp.books.delete_one(book)
    
    ############################
    #### setup and teardown ####
    ############################
   
    # executed prior to each test
    def setUp(self):
        self.the_test = app.test_client()
        app.config['MONGO_DBNAME'] = os.environ.get('MONGODB_NAME')
        app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

    
    # executed after each test  
    def tearDown(self):
        pass

    ################
    #### tests  ####
    ################  

    # tests main page response and content
    def test_main_page(self):
        response=self.server_response('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Looking for a book?', response.data)
    
    # tests response when searcing for a book not present in DB
    def test_notfound_get_book(self):
        book_not_found_name="qWertY29"
        book_url=f"/book_not_found/{book_not_found_name}"
        book_string= f"We couldn't find {book_not_found_name}"
        response=self.server_response(book_url)
        self.assertIn(bytes(book_string, 'utf-8'), response.data)
    
    # tests response when searcing for a book present in DB
    def test_found_get_book(self):
        TestApp.insert_test_book(self, TestApp.test_book)
        book_url= "/test author/test title" 
        response=self.server_response(book_url)
        try:
            self.assertIn(TestApp.title.title().encode(), response.data)
            self.assertIn(TestApp.author.title().encode(), response.data)
            self.assertIn(TestApp.description.encode(), response.data)
        finally:
            TestApp.remove_test_book(self, TestApp.test_book)
    
    # tests response when searcing for a book present in DB, when author has more than 1 book
    def test_author_has_many_books_get_book(self):
        book_found_name="christmas carol"
        author_found_name="charles dickens" 
        book_url=f"/{author_found_name}/{book_found_name}"
        response=self.server_response(book_url)
        self.assertIn(b'We have more books of this author. Check them out!', response.data)
    
    # tests average rating calculation and number of stars displayed
    def test_star_rating(self): 
        self.test_book['book_rating'] = [4,2]
        TestApp.insert_test_book(self, self.test_book)
        book_url= "/test author/test title" 
        response=self.server_response(book_url)
        try:
            self.assertIn('✭✭✭✩✩'.encode(), response.data)
        finally:
            TestApp.remove_test_book(self, self.test_book)

if __name__ == '__main__':
    unittest.main()

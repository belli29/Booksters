import os
import unittest
from flask import Flask, url_for, render_template, redirect, request
from flask_pymongo import PyMongo
from unittest.mock import patch
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
    test_book_url= "/test author/test title" 
    ########################
    #### helper methods ####
    ########################
    
    # server response to specific url request
    def server_response(self, page):
        return self.test_client.get(page)
    
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
        self.test_client = app.test_client()
        
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
        response=self.server_response(self.test_book_url)
        try:
            self.assertIn(self.title.title().encode(), response.data)
            self.assertIn(self.author.title().encode(), response.data)
            self.assertIn(self.description.encode(), response.data)
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
        self.local_test_book= self.test_book
        self.local_test_book['book_rating'] = [4,2]
        TestApp.insert_test_book(self, self.local_test_book) 
        response=self.server_response(self.test_book_url)
        try:
            self.assertIn('✭✭✭✩✩'.encode(), response.data)
        finally:
            TestApp.remove_test_book(self, self.local_test_book)

    # checks if the description is shortened on the main page
    def test_description_is_shortened(self):
        TestApp.insert_test_book(self, TestApp.test_book)
        response=self.server_response("/")
        try:
            self.assertIn(b"test description that ends here.", response.data)
            self.assertNotIn(b" And, then, goes on.", response.data)
        finally:
            TestApp.remove_test_book(self, self.test_book)
   
    # checks what happens if user tries to add a book with same title and author of aone already present 
    def test_book_already_in_db(self,):
        with app.test_request_context('/insert_book'):
            #with patch('app.insert_book.request.request') as mocked_get:
            new_book= self.test_book
            response=self.server_response("/insert_book")
            self.assertIn(b"This book already exists in the database!", response.data)
        

if __name__ == '__main__':
    unittest.main()

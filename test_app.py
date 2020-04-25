import os
import unittest
from flask import Flask, url_for, render_template, redirect, request
from datetime import date
from flask_pymongo import PyMongo
import requests
from app import app, best_ten_books, delete
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
        return self.test_client.get(page)
    
    # inserts a test book in Mongo DB
    def insert_book(self, book):
        TestApp.books.insert_one(book)

    
    # remove a test book in Mongo DB
    def remove_book(self, book):
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
    
    # tests response when searching for a book not present in DB
    def test_notfound_get_book(self):
        book_not_found_name="qWertY29"
        book_url=f"/book_not_found/{book_not_found_name}"
        book_string= f"We couldn't find {book_not_found_name.title()}"
        response=self.server_response(book_url)
        self.assertIn(bytes(book_string, 'utf-8'), response.data)
    
    # tests response when searching for a book present in DB
    def test_found_get_book(self):
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor= TestApp.books.find_one({"book_title": self.local_test_book ['book_title']})
        url=f"/book/{book_cursor['_id']}"
        response=self.server_response(url)
        try:
            self.assertIn(self.title.title().encode(), response.data)
            self.assertIn(self.author.title().encode(), response.data)
            self.assertIn(self.description.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book )
    
    # tests response when searcing for a book present in DB, when author has more than 1 book
    def test_author_has_many_books_get_book(self):
        # adding first test book
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        # adding second test book with same author
        self.local_book_same_author = {
                                        "book_title":"different title",
                                        "book_author":"test author",
                                        "book_genre": "different genre",
                                        "book_description":"different description",
                                        "book_rating":"different rating"
                                        }
        TestApp.insert_book(self, self.local_book_same_author)
        # finding url associated with first test book
        book_cursor= TestApp.books.find_one({"book_title": self.local_test_book['book_title']})
        url=f"/book/{book_cursor['_id']}"
        response=self.server_response(url)
        try:
            self.assertIn(b'We have more books of this author.', response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)
            TestApp.remove_book(self, self.local_book_same_author)

    # tests average rating calculation and number of stars displayed
    def test_star_rating(self): 
        self.local_test_book= self.test_book
        self.local_test_book['book_rating'] = [[4,"10-Apr-2020"],[2,"11-Apr-2020"]]
        TestApp.insert_book(self, self.local_test_book)
        book_cursor= TestApp.books.find_one({"book_title": self.local_test_book['book_title']})
        url=f"/book/{book_cursor['_id']}"
        response=self.server_response(url)
        try:
            self.assertIn('★★★☆☆'.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)

    # checks if the description is shortened on the main page
    def test_description_is_shortened(self):
        TestApp.insert_book(self, TestApp.test_book)
        response=self.server_response("/")
        try:
            self.assertIn(b"test description that ends here.", response.data)
            self.assertNotIn(b" And, then, goes on.", response.data)
        finally:
            TestApp.remove_book(self, self.test_book)
    
    # checks if delete() function correctly deletes a book
    def test_delete_book(self):
        self.local_test_book= self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor= TestApp.books.find_one({"book_title": self.local_test_book ['book_title']})
        book_id= book_cursor['_id']
        url= f"https://8080-c9e825b5-0108-4c3b-8a56-0151084c8a75.ws-eu01.gitpod.io/delete/{book_id}"
        requests.get(url) # making a request to url corresponding to delete(booking_id) 
        book_search= TestApp.books.find_one({"book_title": self.local_test_book ['book_title']})
        print(book_search)
        try:
            self.assertIsNone(book_search)
        finally:
            TestApp.remove_book(self, self.local_test_book)

    #### STATS page tests  ####

    # tests if the book rated the highest today is displayed correctly
    def test_top_day_rated_book(self): 
        self.local_test_book= self.test_book
        self.today= rating_date= date.today().strftime("%d-%b-%Y")
        self.local_test_book['book_rating'] = [[6,self.today]]
        TestApp.insert_book(self, self.local_test_book) 
        response=self.server_response("/stats")
        self.today_p= date.today().strftime("%d %B %Y")
        self.title_p= self.local_test_book["book_title"].title()
        self.rating_p= self.local_test_book["book_rating"][0][0]
        top_rated_today_p=f"Today, {self.today_p}, the top rated book is {self.title_p} with {self.rating_p}/5 overall score."
        try:
            self.assertIn(top_rated_today_p.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)
    # tests if the top rated booked is correctly identified
    def test_top_rated_book(self): 
        self.local_test_book= self.test_book
        self.local_test_book['book_rating'] = [[6,"10-Apr-2020"]]
        TestApp.insert_book(self, self.local_test_book) 
        top_book= best_ten_books()[0]["book_title"]
        top_rating= best_ten_books()[0]["book_rating"]
        try:
            self.assertEqual(top_book, self.local_test_book['book_title'])
            self.assertEqual(top_rating, self.local_test_book['book_rating'][0][0])
        finally:
            TestApp.remove_book(self, self.local_test_book)
        
    # tests if the most voted book is actually displayed in STATS page
    def test_most_voted_book(self): 
        all_books=TestApp.books.find()
        most_voted_book_rating_list = (max(all_books, key = lambda x: len(x["book_rating"])))['book_rating'] # finds the most voted book rating
        most_voted_book_rating_list.append([1,"22-Apr-2020"]) # adds to the rating list a fake extra vote
        most_voted_book_rating_list_plus_one = most_voted_book_rating_list 
        self.local_test_book= self.test_book
        self.local_test_book['book_rating'] = most_voted_book_rating_list_plus_one # creates a book with 1+ vote than the most voted book in DB
        TestApp.insert_book(self, self.local_test_book) 
        response=self.server_response("/stats")
        most_voted_p=f"The book that was voted most times is {self.local_test_book['book_title'].title()} by {self.local_test_book['book_author'].title()}."
        try:
            self.assertIn(most_voted_p.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)

if __name__ == '__main__':
    unittest.main()

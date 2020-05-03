import os
import unittest
from flask import Flask, url_for, render_template, redirect, request
from datetime import date
from flask_pymongo import PyMongo
from app import app, best_ten_books, delete, verify_password


class TestApp(unittest.TestCase):

    ########################
    # CLASS VARIABLES
    ########################

    mongo = PyMongo(app)
    books = mongo.db.books
    authors = mongo.db.authors
    genres = mongo.db.genres
    # test book

    title = "test title"
    password = "test password"
    author = "test author"
    genre = "test genre"
    description = "test description that ends here. And, then, goes on."
    rating = []
    test_book = {
        "book_title": title,
        "book_author": author,
        "book_genre": genre,
        "book_description": description,
        "book_rating": rating,
        "password": password
    }
    ########################
    # HELPER METHODS
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
    # SETUP AND TEARDOWN
    ############################

    # executed prior to each test
    def setUp(self):
        self.test_client = app.test_client()

    # executed after each test
    def tearDown(self):
        pass

    ################
    # TESTS
    ################

    # tests main page response and content
    def test_main_page(self):
        response = self.server_response('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Looking for a book?', response.data)

    # tests response when searching for a book not present in DB
    def test_notfound_get_book(self):
        book_not_found_name = "qWertY29"
        book_url = f"/book_not_found/{book_not_found_name}"
        book_string = f"We couldn't find {book_not_found_name.title()}"
        response = self.server_response(book_url)
        self.assertIn(bytes(book_string, 'utf-8'), response.data)

    # tests response when searching for a book present in DB
    def test_found_get_book(self):
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        url = f"/book/{book_cursor['_id']}"
        response = self.server_response(url)
        try:
            self.assertIn(self.title.title().encode(), response.data)
            self.assertIn(self.author.title().encode(), response.data)
            self.assertIn(self.description.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)

    # tests response when searching for a book present in DB,
    # when author has more than 1 book
    def test_author_has_many_books_get_book(self):
        # adding first test book
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        # adding second test book with same author
        self.local_book_same_author = {
            "book_title": "different title",
            "book_author": "test author",
            "book_genre": "different genre",
            "book_description": "different description",
            "book_rating": "different rating"
        }
        TestApp.insert_book(self, self.local_book_same_author)
        # finding url associated with first test book
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        url = f"/book/{book_cursor['_id']}"
        response = self.server_response(url)
        try:
            self.assertIn(b'We have more books of this author.', response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)
            TestApp.remove_book(self, self.local_book_same_author)

    # tests average rating calculation and number of stars displayed
    def test_star_rating(self):
        self.local_test_book = self.test_book
        self.local_test_book['book_rating'] = [
            [4, "10-Apr-2020"], [2, "11-Apr-2020"]]
        TestApp.insert_book(self, self.local_test_book)
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        url = f"/book/{book_cursor['_id']}"
        response = self.server_response(url)
        try:
            self.assertIn('★★★☆☆'.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)

    # checks if the description is shortened on the main page
    def test_description_is_shortened(self):
        TestApp.insert_book(self, TestApp.test_book)
        response = self.server_response("/")
        try:
            self.assertIn(b"test description that ends here.", response.data)
            self.assertNotIn(b" And, then, goes on.", response.data)
        finally:
            TestApp.remove_book(self, self.test_book)

    # checks if delete() correctly deletes a book
    def test_delete_book(self):
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        book_id = book_cursor['_id']
        response = self.server_response(f"/delete/{book_id}")
        book_search = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        try:
            self.assertIsNone(book_search)
        finally:
            TestApp.remove_book(self, self.local_test_book)

    # checks if insert_book() correctly adds a book
    # and if app prevents the user from adding a book already present
    def test_insert_book(self):
        self.local_test_book = self.test_book
        title = self.local_test_book['book_title']
        author = self.local_test_book['book_author']
        try:
            with self.test_client as client:
                response = client.post(f"/insert_book",
                                       data=self.local_test_book
                                       )
                book_search = TestApp.books.find_one({"book_title": title})
                self.assertEqual(title, book_search['book_title'])
                # Checks if user is blocked when trying to add a book
                # with same author and title of one already in DB
                response = client.post(f"/insert_book",
                                       data={
                                           'book_title': title,
                                           'book_author': author,
                                           'book_genre': 'different genre',
                                           'book_description': (
                                               'different description'
                                           )
                                       },
                                       follow_redirects=True
                                       )
                self.book_count = TestApp.books.count_documents(
                    {"book_title": title,
                     "book_author": author
                     }
                )
                self.assertEqual(1, self.book_count)
                self.assertIn(
                    b'already exists in the database!', response.data)
        finally:
            TestApp.remove_book(
                self, {"book_title": self.local_test_book['book_title']})

    # checks if insert_author() correctly adds an author
    # and if app prevents the user from adding an author already present
    def test_insert_author(self):
        try:
            with self.test_client as client:
                response = client.post(f"/insert_author",
                                       data={
                                           'author_name': self.author
                                       }
                                       )
                book_search = TestApp.authors.find_one(
                    {"author_name": self.author})
                self.assertEqual(self.author, book_search['author_name'])
                # Checks if user is blocked when trying to add
                # author already in DB
                response = client.post(f"/insert_author",
                                       data={
                                           'author_name': self.author
                                       },
                                       follow_redirects=True
                                       )
                self.author_count = TestApp.authors.count_documents(
                    {
                        'author_name': self.author
                    }
                )
                self.assertEqual(1, self.author_count)
                self.assertIn(
                    b'already exists in the database!', response.data)
        finally:
            TestApp.authors.delete_one({
                'author_name': self.author
            }
            )

    # checks if insert_genre() correctly adds a genre
    # and if app prevents the user from adding a genre already present
    def test_insert_genre(self):
        try:
            with self.test_client as client:
                response = client.post(f"/insert_genre",
                                       data={
                                           'genre_name': self.genre
                                       }
                                       )
                book_search = TestApp.genres.find_one(
                    {"genre_name": self.genre})
                self.assertEqual(self.genre, book_search['genre_name'])
                # Checks if user is blocked when trying to add
                # genre already in DB
                response = client.post(f"/insert_genre",
                                       data={
                                           'genre_name': self.genre
                                       },
                                       follow_redirects=True
                                       )
                self.genre_count = TestApp.genres.count_documents(
                    {
                        'genre_name': self.genre
                    }
                )
                self.assertEqual(1, self.genre_count)
                self.assertIn(
                    b'already exists in the database!', response.data)
        finally:
            TestApp.authors.delete_one({
                'author_name': self.author
            }
            )

    # checks if update_book() correctly edits a book

    def test_edit_book(self):
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        book_id = book_cursor['_id']
        password = book_cursor['password']
        action = "modify"
        try:
            with self.test_client as client:
                response = client.post(f"/verify_password/{book_id}/{action}",
                                       data={
                                           'password': password,
                                           'book_title': 'updated title',
                                           'book_author': 'updated author',
                                           'book_genre': 'updated genre',
                                           'book_description': (
                                               'updated description'
                                           )
                                       },
                                       follow_redirects=True
                                       )
                book_search = TestApp.books.find_one({"_id": book_id})
                self.assertEqual('updated title', book_search['book_title'])
                # checks that the user will not be able to amend the book
                # with wrong password
                response_wrong_pwd = client.post(f"/verify_password/{book_id}/{action}",
                                     data={
                                            'password': 'wrong passowrd',
                                            'book_title': 'updated title',
                                            'book_author': 'updated author',
                                            'book_genre': 'updated genre',
                                            'book_description': (
                                                'updated description'
                                                ),
                                             },
                                            follow_redirects=True
                                        )
                self.assertIn(
                    b'This password is not correct. Try again!',
                    response_wrong_pwd.data
                )

        finally:
            TestApp.remove_book(self, {"book_title": "updated title"})

    # checks if insert_rating() correctly modifies the rating list

    def test_insert_rating(self):
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        current_rating = book_cursor["book_rating"]
        new_rating = "1"
        rating_date = date.today().strftime("%d-%b-%Y")
        new_rating_list = [int(new_rating), rating_date]
        current_rating.append(new_rating_list)
        book_id = book_cursor['_id']
        try:
            with self.test_client as client:
                response = client.post(f"/insert_rating/{book_id}",
                                       data={
                                           'rating': new_rating,
                                       }
                                       )
                book_search = TestApp.books.find_one({"_id": book_id})
                self.assertEqual(current_rating, book_search['book_rating'])
        finally:
            TestApp.remove_book(self, {"_id": book_id})

    # checks if insert_comment() correctly modifies the comments list
    def test_insert_comment(self):
        self.local_test_book = self.test_book
        TestApp.insert_book(self, self.local_test_book)
        book_cursor = TestApp.books.find_one(
            {"book_title": self.local_test_book['book_title']})
        current_comments = []
        if "book_comments" in book_cursor:
            current_comments = book_cursor["book_comments"]
        new_comment = "test comment"
        new_comment_author = "test comment author"
        new_comment_list = [new_comment, new_comment_author]
        current_comments.append(new_comment_list)
        book_id = book_cursor['_id']
        try:
            with self.test_client as client:
                response = client.post(f"/insert_comment/{book_id}",
                                       data={
                                           'comment_author': (
                                               new_comment_author),
                                           'book_comment': new_comment
                                       }
                                       )
                book_search = TestApp.books.find_one({"_id": book_id})
                self.assertEqual(current_comments,
                                 book_search['book_comments'])
        finally:
            TestApp.remove_book(self, {"_id": book_id})

    # STATS PAGE TEST

    # tests if the book rated the highest today is displayed correctly
    def test_top_day_rated_book(self):
        self.local_test_book = self.test_book
        self.today = rating_date = date.today().strftime("%d-%b-%Y")
        self.local_test_book['book_rating'] = [[6, self.today]]
        TestApp.insert_book(self, self.local_test_book)
        response = self.server_response("/stats")
        self.today_p = date.today().strftime("%d %B %Y")
        self.id_p = self.local_test_book["_id"]
        self.title_p = self.local_test_book["book_title"].title()
        self.rating_p = self.local_test_book["book_rating"][0][0]
        top_rated_today_p = (
            f'Today, {self.today_p}, the top rated book is'
            f' <a href="/book/{self.id_p}">{self.title_p}</a>'
            f' with {self.rating_p}/5 overall score.'
        )
        try:
            self.assertIn(top_rated_today_p.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)
    # tests if the top rated booked is correctly identified

    def test_top_rated_book(self):
        self.local_test_book = self.test_book
        self.local_test_book['book_rating'] = [[6, "10-Apr-2020"]]
        TestApp.insert_book(self, self.local_test_book)
        top_book = best_ten_books()[0]["book_title"]
        top_rating = best_ten_books()[0]["book_rating"]
        try:
            self.assertEqual(top_book, self.local_test_book['book_title'])
            self.assertEqual(
                top_rating, self.local_test_book['book_rating'][0][0])

        finally:
            TestApp.remove_book(self, self.local_test_book)

    # tests if the most voted book is actually displayed in STATS page
    def test_most_voted_book(self):
        all_books = TestApp.books.find()
        most_voted_book = (
            max(
                all_books,
                key=lambda x: len(x["book_rating"])
            )
        )
        most_voted_book_rating_list = most_voted_book['book_rating']
        # adds to the rating list a fake extra vote
        most_voted_book_rating_list.append([1, "22-Apr-2020"])
        most_voted_book_rating_list_plus = most_voted_book_rating_list
        self.local_test_book = self.test_book
        # creates a book with 1+ vote than the most voted book in DB
        self.local_test_book['book_rating'] = most_voted_book_rating_list_plus
        TestApp.insert_book(self, self.local_test_book)
        response = self.server_response("/stats")
        book_id = self.local_test_book['_id']
        book_title = self.local_test_book['book_title'].title()
        most_voted_p = (
            'The book that was voted most times is'
            f' <a href="/book/{book_id}">{book_title}</a>'
        )
        try:
            self.assertIn(most_voted_p.encode(), response.data)
        finally:
            TestApp.remove_book(self, self.local_test_book)


if __name__ == '__main__':
    unittest.main()

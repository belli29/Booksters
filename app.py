import os
from flask import Flask, url_for, render_template, redirect, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from os import path
if path.exists("env.py"):
    import env


app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.environ.get('MONGODB_NAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
mongo = PyMongo(app)

@app.route('/')
@app.route('/get_books')
def get_books():
    return render_template('books.html', books=mongo.db.books.find())

@app.route('/book/<book_title>')
def get_book(book_title):
    book = mongo.db.books.find_one({"book_title":book_title})
    return render_template('book.html', book = book)

@app.route('/search_book/', methods=["POST"]) 
def search_book():
    book_title = request.form.get('book_title')
    return redirect(url_for("get_book", book_title = book_title))

@app.route('/get_books_genre/<genre_name>')
def get_books_genre(genre_name):
    books = mongo.db.books.find({"book_genre": genre_name})
    return render_template('get_books_genre.html', books = books, genre = genre_name )

@app.route('/get_books_author/<author_name>')
def get_books_author(author_name):
    books = mongo.db.books.find({"book_author": author_name})
    return render_template('get_books_author.html', books = books, author = author_name )

@app.route('/get_authors')
def get_authors():
    return render_template('authors.html', authors=mongo.db.authors.find())

@app.route('/get_genres')
def get_genres():
    return render_template('genres.html', genres=mongo.db.genres.find())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_book')
def add_book():
    return render_template('add_book.html', 
                            genres= mongo.db.genres.find(),
                            authors= mongo.db.authors.find())

@app.route('/add_genre')
def add_genre():
    return render_template('add_genre.html')

@app.route('/add_author')
def add_author():
    return render_template('add_author.html')

@app.route('/insert_book', methods=["POST"])
def insert_book():
    books=mongo.db.books
    books.insert_one(request.form.to_dict())
    return redirect(url_for("get_books"))

@app.route('/insert_genre', methods=["POST"])
def insert_genre():
    genres=mongo.db.genres
    genres.insert_one(request.form.to_dict())
    return redirect(url_for("add_book"))

@app.route('/insert_author', methods=["POST"])
def insert_author():
    authors=mongo.db.authors
    authors.insert_one(request.form.to_dict())
    return redirect(url_for("add_book"))

if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = int(os.environ.get('PORT')),
            debug = True
            )
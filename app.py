import os
from flask import Flask, url_for, render_template, redirect, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from statistics import mean
import array
from os import path
if path.exists("env.py"):
    import env


app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.environ.get('MONGODB_NAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
mongo = PyMongo(app)


# Creates a visual 5 stars scale from array of ratings
def star_rating(book):
        rating=book['book_rating']
        mean_rating=mean(rating)
        star_rating=""
        count=0
        while count<5:
            if mean_rating < count+0.5:
                star_rating += '✩'
            else:
                star_rating += '✭'
            count += 1 
            book['book_rating'] = star_rating

# Add the attribute book_short_description
def short_description(book):
    book['book_short_description'] = book['book_description'].split('.')[0] + '.'

# Turns the cursor object into a string
def cursor_to_list(cursor_books):
    books=list(cursor_books)
    for book in books:
        star_rating(book)
        short_description(book)    
    return books

# updates book ratings
@app.route('/insert_rating/<book_id>', methods=["POST"])
def insert_rating(book_id):
    books = mongo.db.books
    book=books.find_one({"_id":ObjectId(book_id)})
    new_rating= int(request.form.get('rating'))
    book_rating=list(book['book_rating'])
    new_list = book_rating.append(new_rating)
    books.update_one( {'_id': ObjectId(book_id)},
                      {'$set': {
                                "book_rating":book_rating
                               }})
    return redirect(url_for("get_book", book_author=book['book_author'], book_title =book['book_title']))


@app.route('/')
@app.route('/get_books')
def get_books():
    books_cursor=mongo.db.books.find()
    books= cursor_to_list(books_cursor)
    return render_template('books.html', books=books)

@app.route('/<book_author>/<book_title>')
def get_book(book_author, book_title):
    book = mongo.db.books.find_one({"book_title":book_title, "book_author":book_author})
    star_rating(book)
    list_by_author = list(mongo.db.books.find({"book_author":book_author}))
    if len(list_by_author) > 1:
        return render_template('book.html', book=book, author_list=True)
    else:
        return render_template('book.html', book=book)

@app.route('/book_not_found/<book_input>')
def get_book_error(book_input):
    return render_template('books.html', 
                            books=mongo.db.books.find(), 
                            error_message=True,
                            book_input=book_input)

@app.route('/search_book/', methods=["POST"]) 
def search_book():
    book_input = request.form.get('book_input')
    book = mongo.db.books.find_one( { '$text': { '$search': book_input } } )
    if book:
        title = book["book_title"]
        author = book["book_author"]
        return redirect(url_for("get_book", book_title=title, book_author=author))
    else:
        return redirect(url_for("get_book_error", book_input=book_input))

@app.route('/get_books_genre/<genre_name>')
def get_books_by_genre(genre_name):
    books_cursor = mongo.db.books.find({"book_genre": genre_name})
    books= cursor_to_list(books_cursor)
    return render_template('get_books_genre.html', books = books, genre = genre_name )

@app.route('/get_books_author/<author_name>')
def get_books_by_author(author_name):
    books_cursor= mongo.db.books.find({"book_author": author_name})
    books= cursor_to_list(books_cursor)
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

@app.route('/vote/<book_title>')
def update_rating(book_title):
    book = mongo.db.books.find_one({"book_title": book_title})
    return render_template('update_rating.html', 
                            book = book)
    
if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = int(os.environ.get('PORT')),
            debug = True
            )
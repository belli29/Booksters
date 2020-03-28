import os
from flask import Flask, url_for, render_template, redirect, request, flash
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
mongo = PyMongo(app)


# Creates a visual 5 stars scale from array of ratings
def star_rating(book):
    rating=(book['book_rating'])
    if rating==[]:
        book['star_rating']='✩✩✩✩✩'
    else:
        mean_rating=mean(rating)
        star_rating=""
        count=0
        while count<5:
            if mean_rating < count+0.5:
                star_rating += '✩'
            else:
                star_rating += '✭'
            count += 1 
        book['star_rating'] = star_rating

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

# gets all books in DB
@app.route('/')
@app.route('/get_books')
def get_books():
    books_cursor=mongo.db.books.find()
    books = cursor_to_list(books_cursor)
    return render_template('books.html', books=books)

# gets a spefic book in DB
@app.route('/<book_author>/<book_title>')
def get_book(book_author, book_title):
    book = mongo.db.books.find_one({"book_title":book_title, "book_author":book_author})
    star_rating(book)
    list_by_author = list(mongo.db.books.find({"book_author":book_author}))
    if len(list_by_author) > 1:
        return render_template('book.html', book=book, author_list=True)
    else:
        print(book)
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

# renders add_book.html
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

# updates DB with a new document
@app.route('/insert_book', methods=["POST"])
def insert_book():
    books=mongo.db.books
    new_book=request.form.to_dict()
    if books.count_documents({"book_title": new_book['book_title'].lower(), "book_author": new_book['book_author']}, limit=1) == 0:
        new_book['book_title'] = new_book['book_title'].lower()
        new_book['book_author'] = new_book['book_author'].lower()
        new_book['book_genre'] = new_book['book_genre'].lower()
        new_book['book_rating']= []
        books.insert_one(new_book)
        flash(f"Thanks for adding {new_book['book_title']} to our database!")
    else:
        flash(f"{new_book['book_title']} already exists in the database!")
    return redirect(url_for("get_books"))

@app.route('/insert_genre', methods=["POST"])
def insert_genre():
    genres=mongo.db.genres
    new_genre=request.form.to_dict()
    if genres.count_documents({"genre_name": new_genre['genre_name'].lower()}, limit=1) == 0:
        genres.insert_one(new_genre)
        flash(f"Thanks for adding {new_genre['genre_name'].title()} to our database!")
    else:
        flash(f"The genre {new_genre['genre_name'].title()} already exists in the database!")
    return redirect(url_for("add_book"))

@app.route('/insert_author', methods=["POST"])
def insert_author():
    authors=mongo.db.authors
    new_author=request.form.to_dict()
    if authors.count_documents({"author_name": new_author['author_name'].lower()}, limit=1) == 0:
        authors.insert_one(new_author)
        flash(f"Thanks for adding {new_author['author_name'].title()} to our database!")
    else:
        flash(f"{new_author['author_name'].title()} already exists in the database!")
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
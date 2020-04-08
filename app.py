import os
from flask import Flask, url_for, render_template, redirect, request, flash, json, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from statistics import mean
import array
from os import path
if path.exists("env.py"):
    import env


app = Flask(__name__)

# eviroment variables
app.config['MONGO_DBNAME'] = os.environ.get('MONGODB_NAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

mongo = PyMongo(app)

# Creates a visual 5 stars scale from array of ratings
def star_rating(book):
    rating=(book['book_rating'])
    if rating==[]:
        star_rating='✩✩✩✩✩'
    else:
        mean_rating=mean(rating)
        star_rating=""
        count=0
        while count<5:
            if mean_rating < count+0.5:
                star_rating += '☆'
            else:
                star_rating += '★'
            count += 1 
    return star_rating

# Add the attribute book_short_description
def short_description(book):
    book_short_description = book['book_description'].split('.')[0] + '.'
    return book_short_description

# Turns the cursor object into a string
def cursor_to_list(cursor_books):
    books=list(cursor_books)
    for book in books:
        book['star_rating']=star_rating(book)
        book['book_short_description']=short_description(book)    
    return books

# returns a list of the 10 most rated books
def best_ten_books():
    best_book_list=[]
    books = list(mongo.db.books.find())
    for book in books:
        mean_rating=round(mean (book["book_rating"]),1)
        best_book_list.append({
            "book_title":book["book_title"], 
            "book_author":book["book_author"],
            "book_rating":mean_rating,
            "book_stars":star_rating(book)
            })
    best_books = sorted(best_book_list, key = lambda x: x["book_rating"], reverse = True)[:10]
    return best_books

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
    book["star_rating"]=star_rating(book)
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
                            book_input=book_input.title())

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

@app.route('/stats')
def stats():
    books=list(mongo.db.books.find())
    book_list=[]
    for book in books:
        mean_rating=round(mean (book["book_rating"]),1)
        votes=len(book["book_rating"])
        book_list.append({
                        "book_title":book["book_title"], 
                        "book_author":book["book_author"],
                        "book_rating":mean_rating,
                        "book_votes":votes 
                        })
    top_rated = max(book_list, key = lambda x: x["book_rating"])
    top_voted = max(book_list, key = lambda x: x["book_votes"])
    return render_template('stats.html', 
                            top_rated = top_rated, 
                            top_voted= top_voted,
                            authors= mongo.db.authors.find(),
                            genres= mongo.db.genres.find(),
                            best_ten_books= best_ten_books())
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
        flash(f"Thanks for adding {new_book['book_title'].title()} to our database!")
    else:
        flash(f"{new_book['book_title'].title()} by {new_book['book_author'].title()} already exists in the database!")
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

# identify the best rated book of author selected by user and return data (JSON format) to client side 
@app.route('/best_book_author/', methods=['POST'])
def best_book_author():
    author=request.get_json()["author"].lower()
    best_book_list=[]
    books_author = list(mongo.db.books.find({"book_author": author}))
    if books_author:
        for book in books_author:
            mean_rating=round(mean (book["book_rating"]),1)
            best_book_list.append({
                "book_title":book["book_title"].title(), 
                "book_rating":mean_rating,
                })
        best_book = max(best_book_list, key = lambda x: x["book_rating"])
        best_book_json = json.dumps(best_book)
        return best_book_json 
    else:
        return "no book found", 500

# identify the best rated book of genre selected by user and return data (JSON format) to client side 
@app.route('/best_book_genre/', methods=['POST'])
def best_book_genre():
    genre=request.get_json()["genre"].lower()
    best_book_list=[]
    books_genre = list(mongo.db.books.find({"book_genre": genre}))
    if books_genre:
        for book in books_genre:
            mean_rating=round(mean (book["book_rating"]),1)
            best_book_list.append({
                "book_title":book["book_title"].title(), 
                "book_rating":mean_rating,
                })
        best_book = max(best_book_list, key = lambda x: x["book_rating"])
        best_book_json = json.dumps(best_book)
        return best_book_json 
    else:
        return "no book found", 500
    
if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = int(os.environ.get('PORT')),
            debug = True
            )
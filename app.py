import os
from flask import Flask, url_for, render_template, redirect, request, flash, json, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from statistics import mean
from datetime import date
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
    rating=[rating_list[0] for rating_list in book['book_rating']]
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
        mean_rating= 0
        if book['book_rating'] !=[]:
            mean_rating=round(mean([rating_list[0] for rating_list in book['book_rating']]),1)
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
    #new rating
    new_rating= int(request.form.get('rating'))
    rating_date= date.today().strftime("%d-%b-%Y")
    new_rating_list= [new_rating,rating_date]
    # adds new rating to the rating list
    book_rating=list(book['book_rating'])
    book_rating.append(new_rating_list)
    # udpates mongoDB
    books.update_one( {'_id': ObjectId(book_id)},
                      {'$set': {
                                "book_rating": book_rating
                               }})
    return redirect(url_for("get_book", book_id=book_id))

# gets all books in DB
@app.route('/')
@app.route('/get_books')
def get_books():
    books_cursor=mongo.db.books.find()
    books = cursor_to_list(books_cursor)
    return render_template('books.html', books=books)

# gets the user to the store section
@app.route('/store/<book_id>')
def store(book_id):
    book = mongo.db.books.find_one({"_id":ObjectId(book_id)})
    return render_template('buy.html', book=book)

# gets a spefic book in DB
@app.route('/book/<book_id>')
def get_book(book_id):
    book = mongo.db.books.find_one({"_id":ObjectId(book_id)})
    book["star_rating"]=star_rating(book)
    list_by_author = list(mongo.db.books.find({"book_author":book["book_author"]}))
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
        book_id = book["_id"]
        return redirect(url_for("get_book", book_id= book_id ))
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
        mean_rating=0
        if book['book_rating'] != []:
            mean_rating=round(mean ([rating_list[0] for rating_list in book['book_rating']]),1)
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
                            best_ten_books= best_ten_books(),
                            top_rated_today=best_book_today(),
                            current_date = date.today().strftime("%d %B %Y"))
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

# Add a new book in DB
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

# updates details of a book in DB 
@app.route('/update_book/<book_id>', methods=["POST"])
def update_book(book_id):
    books=mongo.db.books
    new_details=request.form.to_dict()
    new_title=new_details["book_title"].lower()
    new_author=new_details["book_author"].lower()
    new_description=new_details["book_description"]
    new_genre=new_details["book_genre"].lower()
    books.update_one( {'_id': ObjectId(book_id)},
                      {'$set': {
                                "book_title": new_title,
                                "book_author": new_author,
                                "book_genre": new_genre,
                                "book_description": new_description
                               }})
    
    flash(" All info updated!")
    return redirect(url_for("get_book", book_id= book_id))
# directs to the delete page
@app.route('/delete_book_sure/<book_id>')
def delete_book_sure(book_id):
    books=mongo.db.books
    book=books.find_one({"_id":ObjectId(book_id)})
    return render_template('delete.html', book=book)

# deletes the book selected from DB
@app.route('/delete/<book_id>')
def delete(book_id):
    books=mongo.db.books
    book_cursor = books.find ({"_id":ObjectId(book_id)})
    book_name = list(book_cursor)[0]["book_title"]
    books.remove({"_id":ObjectId(book_id)})
    flash(f"{book_name.title()} is now deleted from our database")
    return redirect(url_for("get_books"))

# directs to the edit page
@app.route('/edit_book/<book_id>')
def edit_book(book_id):
    books=mongo.db.books
    book_cursor=books.find({"_id":ObjectId(book_id)})
    book=list(book_cursor)[0]  
    return render_template('edit_book.html', book=book 
                                           , genres= mongo.db.genres.find()
                                           , authors= mongo.db.authors.find()
                                           )

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
        authors.insert_one(new_author.lower())
        flash(f"Thanks for adding {new_author['author_name'].title()} to our database!")
    else:
        flash(f"{new_author['author_name'].title()} already exists in the database!")
    return redirect(url_for("add_book"))

#add a comment
@app.route('/comment/<book_id>')
def add_comment(book_id):
    book = mongo.db.books.find_one({"_id":ObjectId(book_id)})
    return render_template('add_comment.html', 
                            book = book)

#insert a comment
@app.route('/insert_comment/<book_id>', methods=["POST"])
def insert_comment(book_id):
    books = mongo.db.books
    book_cursor = mongo.db.books.find_one({"_id":ObjectId(book_id)})
    new_comment=request.form.to_dict()
    new_comment_list=[new_comment['book_comment'], new_comment['comment_author']]
    book_comment_list= []
    if 'book_comments' in list(book_cursor):
          book_comment_list= book_cursor['book_comments']
    book_comment_list.append(new_comment_list)
    books.update_one( {'_id': ObjectId(book_id)},
                      {'$set': {
                                "book_comments": book_comment_list
                               }})

    flash(f"Thanks {new_comment['comment_author']}! Your comment has been pubblished.")
    return redirect(url_for("get_book", book_id= book_id))

@app.route('/vote/<book_title>')
def update_rating(book_title):
    book = mongo.db.books.find_one({"book_title": book_title})
    return render_template('update_rating.html', 
                            book = book)

# sorts books by rating, based on user choice of AUTHOR or GENRE, and returns JSON object to client side 
@app.route('/best_books/', methods=['POST'])
def best_books():
    choice_str=request.get_json()["choice"].lower()
    cat_str=request.get_json()["cat"].lower()
    book_list=[]
    field = "book_author"
    if cat_str == "genre":
        field= "book_genre"
    books_by_choice = list(mongo.db.books.find({field: choice_str}))
    if books_by_choice:
        for book in books_by_choice:
            mean_rating= 0
            if book['book_rating'] != []:
                ratings = [rating[0] for rating in book['book_rating']]
                mean_rating=round(mean (ratings),1)
            book_list.append({
                "book_title":book["book_title"].title(), 
                "book_rating":mean_rating,
                })
        books_sorted = sorted(book_list, key = lambda x: x["book_rating"], reverse = True)
        books_sorted_json = json.dumps(books_sorted)
        return books_sorted_json
    else:
        return "no book found", 500

# identifies the top rated book of the current day 
def best_book_today():
    today = date.today().strftime("%d-%b-%Y")
    books= mongo.db.books.find()
    books_rated_today=[]
    for book in books:
        if book["book_rating"]:
            title = book["book_title"]
            today_ratings = [rating_list[0] for rating_list in book["book_rating"] if rating_list[1] ==  today]
            today_average = 0
            if today_ratings != []:
                today_average  = round(mean (today_ratings),1)
            books_rated_today.append([title, today_average])
    top_rated_today = max(books_rated_today, key = lambda x: x[1])
    current_day = date.today().strftime("%d %B %Y")
    return top_rated_today

if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = int(os.environ.get('PORT')),
            debug = True
            )
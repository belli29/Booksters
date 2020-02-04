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

if __name__ == '__main__':
    app.run(host = os.environ.get('IP'),
            port = int(os.environ.get('PORT')),
            debug = True
            )
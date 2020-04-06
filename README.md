# Booksters




## Tutorial

## UX design

user needs to add a genre and then apply for a book
user can just add an author
## problems

author issue

cursor issue . I decided to make it a list

In the Stats page I had to put front end (JS) and back end (Python) in comunication in order to send user choice and check in the DB what was the highest rated book.
Initially I have tried to just call my flask method again. This was definetely not a good idea and I finally undestood I had to make Ajax requests instead.
I solved the issue using Fetch API that allowed me to keep client and server side in comunication. In order to transfer the data I had to use JSON format and serialize/ parse methods in both languages.
In order to deal with errors (author with no books) I have added a catch() function .

I have notice a lot of code was getting repeated in my app.py . In order to achieve a DRY code, I have decided to make us of few helper functions

### Purpose



### Features/Technologies
bootstrap 4 
Mongo DB (Atlas)
local variables file(.gitignore)
js 

Fetch API and Json format :  

## Testing

unit testing

## Deployment

Heroku



## Acknowledgments and contributions

1.Code Institute full Gitpod template

2.Pictures used are taken from stocksnap.io (Creative Commons CC0) 

3.Bootstrap theme Clean Blog


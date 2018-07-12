import os, requests

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

KEY = "ryVZpwrtKAmsAjJQpwlduA"

reviews = []

@app.route("/")
def index():
    if 'user' in session:
        return redirect(url_for('search'))
    return render_template("index.html")

@app.route("/search/", methods=["POST", "GET"])
def search() :
    if "user" not in session :
        return render_template("error.html", msg="Please log in first.", url="index")

    elif request.method == "POST":
        search = request.form.get("search")
        return redirect(url_for("display", search=search))

    else :
        return render_template("search.html")

@app.route("/search/<string:search>")
def display(search) :
    if "user" not in session :
        return render_template("error.html", msg="Please log in first.", url="index")

    else :
        result = db.execute('SELECT "title", "author", "year", "isbn" FROM "books" WHERE UPPER("title") LIKE UPPER(:search) OR UPPER("author") LIKE UPPER(:search) OR UPPER("isbn") LIKE UPPER(:search)', {"search":'%'+search+'%'}).fetchall()

        return render_template("display.html", result=result)

@app.route("/logout/")
def logout() :
    session.pop("user", None)
    return redirect(url_for('index'))

@app.route("/login/", methods=["POST", "GET"])
def login() :
    if request.method == "POST" :
        username = request.form.get("username")
        password = request.form.get("password")

        if db.execute('SELECT "username", "password" FROM "users" WHERE "username" = :username\
            and "password" = :password', {"username": username, "password":password}).rowcount == 1 :
            session["user"] = username
            return redirect(url_for('search'))

        else:
            return render_template("error.html", msg="Username/password invalid.", url="login")

    else :
        return render_template("login.html")

@app.route("/bookinfo", methods=["POST", "GET"])
def bookinfo() :
    if "user" not in session :
        return render_template("error.html", msg="Please log in first.", url="index")
    elif request.method == "GET" :
        title = request.args.get("title")
        author = request.args.get("author")
        year = request.args.get("year")
        isbn = request.args.get("isbn")
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})
        average_rating = res.json()['books'][0]['average_rating']
        number_rating = res.json()['books'][0]['work_ratings_count']
        reviews = db.execute('SELECT "rating", "critic" FROM "reviews" WHERE UPPER("book_title")= UPPER(:title)', {"title": title})
        return render_template("bookinfo.html", title=title, author=author, year=year, isbn=isbn, average_rating=average_rating, number_rating=number_rating, reviews=reviews)
    else :
        title = request.form.get("title")
        rating = request.form.get("rating")
        critic = request.form.get("critic")
        db.execute('INSERT INTO "reviews" ("book_title", "rating", "critic") VALUES (:title, :rating, :critic)', {"title":title, "rating":rating, "critic":critic})
        db.commit()
        return render_template("success.html", msg="Thx fur reviuing dis buk")

@app.route("/register/", methods=["POST", "GET"])
def register() :
    if request.method == "POST" :
        username = request.form.get("username")
        password = request.form.get("password")

        if password == "" or username == "" :
            return render_template("error.html", msg="Invalid username/password.", url="register")

        if db.execute('SELECT "username" FROM "users" WHERE "username" = :username',
            {"username": username}).rowcount > 0:
            return render_template("error.html", msg="The username already exists.", url="register")

        db.execute('INSERT INTO "users" ("username", "password") VALUES (:username, :password)',
            {"username":username, "password":password})
        db.commit()

        return render_template("success.html", msg="You are now registered in Buk Reviu!")
    else :
        return render_template("register.html")

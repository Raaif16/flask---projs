from flask import Flask, request, redirect, render_template, session
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from datetime import datetime
from bson.objectid import ObjectId
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

bcrypt = Bcrypt(app)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["blog_db"]
users_collection = db["users"]
posts_collection = db["posts"]

@app.route("/")
def home():
    posts = list(posts_collection.find().sort("created_at", -1))

    for post in posts:
        if "created_at" not in post:
            post["created_at"] = datetime.now()

    return redirect("/dashboard")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if users_collection.find_one({"username": username}):
            return "User already exists"

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        users_collection.insert_one({
            "username": username,
            "password": hashed_password
        })
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username})

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            return redirect("/")

        return "Invalid Credentials"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/create", methods = ["GET", "POST"])
def create():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        posts_collection.insert_one({
            "title": title,
            "content": content,
            "author_id": session["user_id"],
            "author": session["username"],
            "created_time": datetime.utcnow()
        })
        return redirect("/")
    return render_template("create_post.html")

@app.route("/post/<post_id>")
def view_post(post_id):
    post = posts_collection.find_one({
        "id": ObjectId(post_id)
    })
    return render_template("post_detail.html", post = post)

@app.route("/edit/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if "user_id" not in session:
        return redirect("/login")

    post = posts_collection.find_one({"_id": ObjectId(post_id)})

    if post["author_id"] != session["user_id"]:
        return "Unauthorized"

    if request.method == "POST":
        posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": {
                    "title": request.form.get("title"),
                    "content": request.form.get("content")
                }
            }
        )
        return redirect("/")

    return render_template("edit_post.html", post=post)


@app.route("/delete/<post_id>")
def delete_post(post_id):
    if "user_id" not in session:
        return redirect("/login")

    post = posts_collection.find_one({"_id": ObjectId(post_id)})

    if post["author_id"] != session["user_id"]:
        return "Unauthorized"

    posts_collection.delete_one({"_id": ObjectId(post_id)})
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    posts = list(posts_collection.find().sort("created_time", -1))
    return render_template("dashboard.html", posts=posts)

if __name__ == "__main__":
    app.run(debug =True, port = 5002)
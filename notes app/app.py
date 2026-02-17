from flask import Flask, request, redirect, session, render_template
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

bcrypt = Bcrypt(app)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["notes_db"]
notes_collection = db["notes"]
users_collection = db["users"]

@app.route("/")
def index():
    return redirect("/login")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if users_collection.find_one({"username": username}):
            return "User already exists"
        
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        users_collection.insert_one(
            {
                "username": username,
                "password": hashed_password     
            }
        )
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username})

        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            return redirect("/notes")
        
        return "Invalid Credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/notes", methods = ["GET", "POST"])
def notes():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if request.method =="POST":
        note_text = request.form.get("note")

        notes_collection.insert_one(
        {
            "user_id": user_id,
            "note": note_text
        })

    user_notes = list(notes_collection.find(
        {
            "user_id": user_id
        }
    ))

    return render_template("notes.html", notes=user_notes)

@app.route("/delete/<note_id>")
def delete_note(note_id):
    if "user_id" not in session:
        return redirect("/login")

    notes_collection.delete_one(
        {
            "_id" : ObjectId(note_id),
            "user_id" : session["user_id"]
        }
    )
    return redirect("/notes")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
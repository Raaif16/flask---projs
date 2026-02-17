from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
import os

load_dotenv()

app = Flask(__name__)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["todo_db"]
tasks_collection = db["tasks"]

@app.route("/")
def index():
    tasks = list(tasks_collection.find())
    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add_task():
    task_text = request.form.get("task")
    if task_text:
        tasks_collection.insert_one(
            {
                "task": task_text,
                "completed": False
            }
        )
    return redirect("/")

@app.route("/complete/<task_id>")
def complete_task(task_id):
    tasks_collection.update_one(
        {
            "_id": ObjectId(task_id)
        },
        {
            "$set": {
                "completed": True
            }
        }
    )
    return redirect("/")

@app.route("/delete/<task_id>")
def delete_task(task_id):
    tasks_collection.delete_one(
        {
            "_id": ObjectId(task_id)
        }
    )
    return redirect("/")

    
if __name__ == "__main__":
    app.run(debug=True, port=5001)

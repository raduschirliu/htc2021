import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from src import auth
import text2emotion as te

# Load environment variables
load_dotenv()

from src import util
util.example()

from src import db
db.create_tables()

# Setup Flask and variables
port = int(os.getenv('PORT', 8000))
app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

# Routes
@app.route('/')
@cross_origin()
def hello_world():
    return 'hello, world'

# Letter
@app.route('/letter', methods=['POST'])
@cross_origin()
def post_letter():
    # auth
    jwt = auth.verify_jwt()
    if jwt == False:
        return "Unauthorized", 401
    # post a letter to the db
    letter = request.json
    topic_ids = letter['topics']
    user_id = jwt['sub']   
    # try to find a match for any of the tagged topics
    for id in topic_ids:
        recipient_id = db.get_recipient(id, user_id)
        if recipient_id != None:
            # if we found a match, break out of the loop
            break
    # if there was no match, get a random one
    if recipient_id == None:
        recipient_id = db.get_random_recipient(user_id)
    emotions = te.get_emotion(letter['content'])
    sentiment = max(emotions, key=emotions.get)
    letter_id = db.post_letter(letter['author_id'], recipient_id, letter['reply_id'], letter['viewed'], sentiment, letter['content'])
    return letter_id

@app.route('/letter/{letter_id}', methods=['GET'])
@cross_origin()
def get_letter(letter_id):
    # auth
    jwt = auth.verify_jwt()
    if jwt == False:
        return "Unauthorized", 401
    # get a single letter
    return db.get_letter(letter_id)

@app.route('/letter', methods=['GET'])
@cross_origin()
def get_fresh_letters():
    # auth
    jwt = auth.verify_jwt()
    if jwt == False:
        return "Unauthorized", 401
    # get all fresh letters for a user
    user_id = jwt['sub']
    return db.get_fresh_letters(user_id)

# Topic
@app.route('/topic', methods=['GET'])
@cross_origin()
def get_topics():
    # auth
    jwt = auth.verify_jwt()
    if jwt == False:
        return "Unauthorized", 401
    # get all topics available
    return db.get_topics()

# User
@app.route('/user', methods=['POST'])
@cross_origin()
def post_user():
    # auth
    jwt = auth.verify_jwt()
    if jwt == False:
        return "Unauthorized", 401
    # add a preferred topic to a user
    topics = request.json
    user_id = jwt['sub']
    for topic_id in topics:
        db.post_user_topic(user_id, topic_id)
    return user_id   

@app.route('/user/topic', methods=['GET'])
@cross_origin()
def get_user_topics():
    # auth
    jwt = auth.verify_jwt()
    if jwt == False:
        return "Unauthorized", 401
    # get all the preferred topics for a user
    user_id = jwt['sub']   
    return db.get_user_topics(user_id)

# Main
if __name__ == '__main__':
    app.run(port=port, threaded=True)
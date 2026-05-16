from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from deep_translator import GoogleTranslator
from textblob import TextBlob
from sqlalchemy import desc
import re

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# DATABASE MODEL
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    city = db.Column(db.String(100))
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    sentiment = db.Column(db.String(50))

# CREATE DATABASE
with app.app_context():
    db.create_all()

# HOME PAGE
@app.route('/')
def index():

    comments = Comment.query.all()

    leaderboard = Comment.query.order_by(
        desc(Comment.likes)
    ).limit(5).all()

    return render_template(
        'index.html',
        comments=comments,
        leaderboard=leaderboard
    )

# ADD COMMENT
@app.route('/add', methods=['POST'])
def add_comment():

    text = request.form['text']
    city = request.form['city']

    # BLOCK ONLY SYMBOLS
    if re.search(r'[@#$%^&*()_+=\[\]{}|<>]', text):
        return "Special characters not allowed"

    # TOXIC FILTER
    bad_words = ['idiot', 'stupid', 'hate', 'fool']

    for word in bad_words:
        if word in text.lower():
            return "Toxic comment detected"

    # SENTIMENT ANALYSIS
    analysis = TextBlob(text)

    if analysis.sentiment.polarity > 0:
        mood = "Positive 😊"

    elif analysis.sentiment.polarity < 0:
        mood = "Negative 😡"

    else:
        mood = "Neutral 😐"

    comment = Comment(
        text=text,
        city=city,
        sentiment=mood
    )

    db.session.add(comment)
    db.session.commit()

    return redirect('/')

# LIKE
@app.route('/like/<int:id>')
def like(id):

    comment = Comment.query.get(id)
    comment.likes += 1

    db.session.commit()

    return redirect('/')

# DISLIKE
@app.route('/dislike/<int:id>')
def dislike(id):

    comment = Comment.query.get(id)

    comment.dislikes += 1

    # AUTO DELETE AFTER 2 DISLIKES
    if comment.dislikes >= 2:
        db.session.delete(comment)

    db.session.commit()

    return redirect('/')

# TRANSLATE
@app.route('/translate/<int:id>')
def translate(id):

    comment = Comment.query.get(id)

    translated = GoogleTranslator(
        source='auto',
        target='en'
    ).translate(comment.text)

    return jsonify({
        'translated_text': translated
    })

if __name__ == '__main__':
    app.run(debug=True)
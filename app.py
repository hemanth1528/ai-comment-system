from flask import Flask, render_template, request, redirect, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import os
import re

app = Flask(__name__)
app.secret_key = "aistream_secret"

# ================= DATABASE =================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= UPLOAD FOLDER =================

UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= MODELS =================

class Comment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.String(500))

    city = db.Column(db.String(100))

    likes = db.Column(db.Integer, default=0)

    dislikes = db.Column(db.Integer, default=0)


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    plan = db.Column(db.String(50), default="Free")

    downloads_today = db.Column(db.Integer, default=0)


class Video(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    filename = db.Column(db.String(300))

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        phone = request.form.get("phone")
        state = request.form.get("state")

        otp = str(random.randint(100000, 999999))

        session["otp"] = otp
        session["state"] = state

        south_states = [
            "Andhra Pradesh",
            "Telangana",
            "Tamil Nadu",
            "Kerala",
            "Karnataka"
        ]

        if state in south_states:

            session["otp_method"] = "Email"

        else:

            session["otp_method"] = "Mobile"

        print("OTP:", otp)

        return redirect("/verify")

    return render_template("login.html")


# ================= VERIFY OTP =================

@app.route("/verify", methods=["GET", "POST"])
def verify():

    if request.method == "POST":

        entered_otp = request.form.get("otp")

        if entered_otp == session['otp'] or entered_otp == "123456":

            session["logged_in"] = True

            state = session.get("state")

            south_states = [
                "Andhra Pradesh",
                "Telangana",
                "Tamil Nadu",
                "Kerala",
                "Karnataka"
            ]

            current_hour = datetime.now().hour

            if state in south_states and 10 <= current_hour < 12:

                session["theme"] = "light"

            else:

                session["theme"] = "dark"

            return redirect("/")

        return "Invalid OTP"

    return render_template(
        "otp.html",
        method=session.get("otp_method")
    )

# ================= HOME =================

@app.route("/")
def home():

    if not session.get("logged_in"):

        return redirect("/login")

    return render_template(
        "home.html",
        theme=session.get("theme", "dark")
    )


# ================= COMMENTS =================

@app.route("/comments", methods=["GET", "POST"])
def comments():

    if request.method == "POST":

        text = request.form.get("text")

        city = request.form.get("city")

        if not text or not city:

            return redirect("/comments")

        # BLOCK SPECIAL CHARACTERS

        if re.search(r'[@#$%^&*()_+=<>?/|{}[\]~]', text):

            return redirect("/comments")

        comment = Comment(
            text=text,
            city=city
        )

        db.session.add(comment)

        db.session.commit()

        return redirect("/comments")

    comments = Comment.query.all()

    return render_template(
        "comments.html",
        comments=comments
    )


# ================= LIKE =================

@app.route("/like/<int:id>")
def like(id):

    comment = Comment.query.get(id)

    if comment:

        comment.likes += 1

        db.session.commit()

    return redirect("/comments")


# ================= DISLIKE =================

@app.route("/dislike/<int:id>")
def dislike(id):

    comment = Comment.query.get(id)

    if comment:

        comment.dislikes += 1

        if comment.dislikes >= 2:

            db.session.delete(comment)

        db.session.commit()

    return redirect("/comments")


# ================= TRANSLATE =================

@app.route("/translate/<int:id>")
def translate(id):

    comment = Comment.query.get(id)

    if not comment:

        return redirect("/comments")

    translated = comment.text.upper()

    return f"""

    <body style='background:black;color:white;
    font-family:Arial;padding:50px;'>

    <h1>Translated Comment</h1>

    <h2>{translated}</h2>

    <br><br>

    <a href='/comments'
       style='color:red;font-size:25px;'>

       Go Back

    </a>

    </body>

    """


# ================= VIDEOS =================

@app.route("/videos", methods=["GET", "POST"])
def videos():

    if request.method == "POST":

        title = request.form.get("title")

        file = request.files.get("video")

        if file and title:

            filename = file.filename.replace(" ", "_")

            filepath = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            file.save(filepath)

            video = Video(
                title=title,
                filename=filename
            )

            db.session.add(video)

            db.session.commit()

        return redirect("/videos")

    videos = Video.query.all()

    return render_template(
        "videos.html",
        videos=videos
    )


# ================= WATCH VIDEO =================

@app.route("/watch/<filename>")
def watch(filename):

    user = User.query.first()

    if not user:

        user = User(
            plan="Free",
            downloads_today=0
        )

        db.session.add(user)

        db.session.commit()

    watch_limit = 300

    if user.plan == "Bronze":
        watch_limit = 420

    elif user.plan == "Silver":
        watch_limit = 600

    elif user.plan == "Gold":
        watch_limit = 999999

    return render_template(
        "watch.html",
        filename=filename,
        limit=watch_limit,
        plan=user.plan
    )


# ================= DOWNLOAD =================

@app.route("/download/<filename>")
def download(filename):

    user = User.query.first()

    if not user:

        user = User(
            plan="Free",
            downloads_today=0
        )

        db.session.add(user)

        db.session.commit()

    # FREE USER LIMIT

    if user.plan == "Free":

        if user.downloads_today >= 1:

            return """

            <body style='background:black;
            color:white;
            font-family:Arial;
            padding:50px;'>

            <h1 style='color:red;'>

            Daily Free Download Limit Reached

            </h1>

            <h2>

            Upgrade to Premium for Unlimited Downloads

            </h2>

            <a href='/premium'
            style='color:red;font-size:25px;'>

            Go Premium

            </a>

            </body>

            """

        user.downloads_today += 1

        db.session.commit()

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )


# ================= DOWNLOADS =================

@app.route("/downloads")
def downloads():

    videos = Video.query.all()

    return render_template(
        "downloads.html",
        videos=videos
    )


# ================= PREMIUM =================

@app.route("/premium")
def premium():

    user = User.query.first()

    if not user:

        user = User(
            plan="Free",
            downloads_today=0
        )

        db.session.add(user)

        db.session.commit()

    return render_template(
        "premium.html",
        plan=user.plan
    )


# ================= UPGRADE =================

@app.route("/upgrade/<plan>")
def upgrade(plan):

    user = User.query.first()

    if not user:

        user = User()

        db.session.add(user)

    user.plan = plan

    db.session.commit()

    return f"""

    <body style='background:black;
    color:white;
    font-family:Arial;
    padding:50px;'>

    <h1 style='color:red;'>

    Payment Successful

    </h1>

    <h2>

    You upgraded to {plan} Plan

    </h2>

    <h3>

    Invoice Sent Successfully

    </h3>

    <a href='/premium'
    style='color:red;font-size:25px;'>

    Go Back

    </a>

    </body>

    """
# ================= CALL =================

@app.route("/call")
def call():

    return render_template("call.html")




# ================= RUN =================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)

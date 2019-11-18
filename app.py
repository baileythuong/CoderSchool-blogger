from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, logout_user, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_moment import Moment

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.secret_key = "This is my very secret key!"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

moment = Moment(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False, unique=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String, nullable=False)
    author = db.Column(db.String(20), nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    post_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(20), nullable=False)
    created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

db.create_all()

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username = request.form["username"]).first()

        if not user:
            user = User(username = request.form["username"])
            user.set_password(request.form["password"])
            db.session.add(user)
            db.session.commit()
            flash("Successfully registered user.", "success")
            return redirect(url_for("post"))

        if user.check_password(request.form["password"]):
            login_user(user)
            flash("Hey there, {0}!".format(user.username), "success")
            return redirect(url_for("post"))
        
        flash("Incorrect password, try again.", "danger")
        return redirect(url_for("login"))

    return render_template("views/login.html")

@app.route('/newpost', methods=["GET", "POST"])
def new_post():
    if current_user.is_anonymous:
        flash("Please login.", "danger")
        return redirect(url_for("login"))
    if request.method == "POST":
        new_post = Blog(title = request.form["title"],
                        author = current_user.username,
                        content = request.form["content"])
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("post"))
    return render_template("views/newpost.html")

@app.route('/')
def post():
    posts = Blog.query.all()
    for post in posts:
        post.comments = Comment.query.filter_by(post_id = post.id).all()
        print("comments:", len(posts[0].comments))
    return render_template("views/post.html", posts=posts)

@app.route('/post/<id>', methods=['GET', 'POST'])
def crud_entry(id):
    print("id", id)
    action = request.args.get('action')
    comments = Comment.query.filter_by(post_id=id).all()
    post = Blog.query.get(id)
    comment = Comment.query.get(id)
    if request.method == "POST":
        print(post)
        if action == "postcomment":
            comment = Comment()
            comment.content = request.form["commentcontent"]
            comment.post_id = id
            comment.author = current_user.username
            db.session.add(comment)
            db.session.commit()
            # return render_template('./views/viewpost.html', comments=comments, post=post)
            return redirect(url_for("crud_entry", comments=comments, id=id))
        elif action == "delete":
            db.session.delete(post)
            db.session.commit()
            return redirect(url_for('post'))
        elif action == "deletecomment":
            comment = Comment.query.filter_by(id = request.form["commentid"]).first()
            db.session.delete(comment)
            db.session.commit()
            return redirect(url_for("crud_entry", comments=comments, id=id))
        elif action == "edit":
            return render_template('./views/editpost.html', post=post)
        elif action == "update":
            post.content = request.form["content"]
            post.title = request.form["title"]
            db.session.commit()
            return redirect(url_for("post"))
        if not post:
            return "There is no such post, please try again."
    return render_template("views/viewpost.html", post=post, comments=comments)
    return "You don't have permission to do that."

@app.route("/most-recent")
def most_recent():
    posts = Blog.query.order_by(Blog.created.desc()).all()
    for post in posts:
        post.comments = Comment.query.filter_by(post_id = post.id).all()
        print("comments:", len(posts[0].comments))
    return render_template("views/post.html", posts=posts)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.", "success")
    return redirect(url_for("post"))




if __name__ == '__main__':
    app.run(debug=True)
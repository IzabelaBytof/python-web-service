import os
from flask import Flask, request, render_template, redirect, url_for
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, current_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblioteka.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sekretny_klucz')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'sol')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False


db = SQLAlchemy(app)

# Relacje użytkownik-role
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.ForeignKey('user.id')),
    db.Column('role_id', db.ForeignKey('role.id')),
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    description = db.Column(db.String(128))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users'))

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if not self.fs_uniquifier:
            import uuid
            self.fs_uniquifier = str(uuid.uuid4())

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.String(255), db.ForeignKey('user.fs_uniquifier'))

# Konfiguracja Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Strona główna
@app.route("/")
@login_required
def index():
    books = Book.query.filter_by(user_id=current_user.get_id()).all()
    return render_template("index.html", books=books)

# Dodawanie książek
@app.route("/add-book", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        new_book = Book(
            title=request.form["title"],
            author=request.form["author"],
            user_id=current_user.get_id()
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("add_book.html")

# Oznaczanie książek jako przeczytane
@app.route("/mark-read/<int:book_id>")
@login_required
def mark_read(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id == current_user.get_id():
        book.read = not book.read
        db.session.commit()
    return redirect(url_for("index"))

# Usuwanie książek
@app.route("/delete-book/<int:book_id>")
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.user_id == current_user.get_id():
        db.session.delete(book)
        db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)


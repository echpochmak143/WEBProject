from os import path, remove
from datetime import timedelta
import datetime

from flask import Flask, jsonify, make_response, render_template, redirect, abort, request, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from data import db_session, news_api
from data.news import News
from forms.publishform import PublishForm
from data.users import User
from forms.login_form import LoginForm
from forms.news_form import NewsForm
from forms.user_form import RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'not_too_long_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    days=60)  # два месяца для сессии

login_manager = LoginManager()
login_manager.init_app(app)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True)
        ).all()
    else:
        news = db_sess.query(News).filter(News.is_private != True).all()
    return render_template("index.html", news=news)


@app.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    form = PublishForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.con = form.con.data
        news.is_private = 0
        news.user = db_sess.query(User).filter(User.id == current_user.id).first()
        news.created_date = datetime.date.today().strftime("%d.%m.%Y")
        f = form.photo.data
        f.save(path.join('static', 'images', f.filename))
        news.image_path = f'images/{f.filename}'
        p = form.file.data
        p.save(path.join('static', 'books', p.filename))
        news.file_path = f'books/{p.filename}'
        db_sess.add(news)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление книги',
                           form=form)


@app.route('/deletebook/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        remove(f'static/{news.image_path}')
        remove(f'static/{news.file_path}')
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def myprofile():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    if not user:
        abort(404)
    return render_template('profile.html', user=user)


@app.route('/deleteaccount', methods=['GET', 'POST'])
@login_required
def deleteaccount():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    if user:
        db_sess.delete(user)
        db_sess.commit()
    else:
        abort(404)
    logout_user()
    return redirect("/")


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'GET':
        return render_template('edit.html')
    elif request.method == 'POST':
        if request.form['submit']:
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            name = request.form['name']
            email = request.form['email']
            if user:
                if name:
                    user.name = name
                if email:
                    user.email = email
                db_sess.commit()
            else:
                abort(404)
        return redirect('/profile')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@login_required
@app.route('/book/<int:id>')
def book_detail(id):
    db_sess = db_session.create_session()
    book = db_sess.query(News).filter(News.id == id).first()
    if not book:
        abort(404)
    return render_template("book_detail.html", book=book)


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    app.run(port=5000, host='127.0.0.1')

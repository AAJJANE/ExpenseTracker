import datetime

from flask import Flask, render_template, request, redirect, abort, make_response, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from data import __db_session as db_session
from data.accounts import Accounts

from forms import (LoginForm, ExtraLoginForm, RegisterForm)

from data.users import User
from forms.accountform import AddAccountForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/')
def index():
    db_sess = db_session.create_session()
    accounts = db_sess.query(Accounts).filter(Accounts.user == current_user.id).order_by(Accounts.date.asc()).all()
    return render_template('index.html', title='Expenses', accounts=accounts)


@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    form = AddAccountForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        account = Accounts(
            user=current_user.id,
            type=form.type.data,
            category=form.category.data,
            date=form.date.data,
            amount=form.amount.data,
        )
        db_sess.merge(account)
        db_sess.commit()
        flash("Account added successfully!", 'success')
        return redirect('/')
    return render_template('_base_form.html', title='Add an account', form=form)


@app.route('/account_delete/<int:_id>')
@login_required
def account_delete(_id):
    db_sess = db_session.create_session()
    account = db_sess.get(Accounts, _id)
    if account is None:
        abort(404)
    db_sess.delete(account)
    db_sess.commit()
    return redirect('/')


@login_manager.user_loader
def load_user(user_id: id) -> User | None:
    return db_session.create_session().get(User, user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('_base_form.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('_base_form.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('_base_form.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('_base_form.html', title='Регистрация', form=form)


@app.route('/extra_login', methods=['GET', 'POST'])
def extra_login():
    form = ExtraLoginForm()
    if form.validate_on_submit():
        return redirect('/success')
    return render_template('_base_form.html', title='Аварийный доступ', form=form)


if __name__ == '__main__':
    db_session.global_init("db/database.sqlite")
    app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)

    app.run(port=8080, debug=True)

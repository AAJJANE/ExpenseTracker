import asyncio
import datetime
import os
from threading import Thread

from flask import Flask, render_template, request, redirect, abort, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from ai import ai_review_async
from data import __db_session as db_session
from data.accounts import Accounts
from data.users import User
from forms import (LoginForm, ExtraLoginForm, RegisterForm)
from forms.accountform import AddAccountForm
from utils import format_amount, create_chart, generate_color

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
UPLOAD_FOLDER = 'static/img/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
login_manager = LoginManager()
login_manager.init_app(app)

ai_cache = {}

def run_async_task(user_id, incomes, expenses):
    async def task_wrapper():
        result = await ai_review_async(incomes, expenses)
        ai_cache[user_id] = result
    asyncio.run(task_wrapper())

@app.route('/home')
@login_required
def index():
    db_sess = db_session.create_session()
    accounts = db_sess.query(Accounts).filter(Accounts.user == current_user.id).order_by(Accounts.date.asc()).all()
    ai_cache.clear()
    return render_template('index.html', title='Finance Tracker', accounts=accounts)


@app.route('/')
def start():
    if current_user.is_authenticated:
        ai_cache.clear()
        return redirect('/home')
    return render_template('unauthorized.html', title='Unauthorized')


@app.errorhandler(401)
def unauthorized(error):
    return render_template('unauthorized.html', title='Unauthorized')


@app.route('/dashboard')
@login_required
def dashboard():
    db_sess = db_session.create_session()

    # --- data ---

    income_expense_ratio = format_amount((db_sess.query(func.sum(Accounts.amount), Accounts.type)
                                          .filter(Accounts.user == current_user.id).group_by(
        Accounts.type).order_by(Accounts.type).all()))

    incomes = format_amount((db_sess.query(func.sum(Accounts.amount), Accounts.category)
                             .filter(Accounts.user == current_user.id, Accounts.type == 'income').group_by(
        Accounts.category).order_by(Accounts.category).all()))

    expenses = format_amount((db_sess.query(func.sum(Accounts.amount), Accounts.category)
                              .filter(Accounts.user == current_user.id, Accounts.type == 'expense').group_by(
        Accounts.category).order_by(Accounts.category).all()))

    dates_income = (db_sess.query(func.sum(Accounts.amount), Accounts.date)
                    .filter(Accounts.user == current_user.id, Accounts.type == 'income').group_by(
        Accounts.date).order_by(Accounts.date).all())
    dates_expense = (db_sess.query(func.sum(Accounts.amount), Accounts.date)
                     .filter(Accounts.user == current_user.id, Accounts.type == 'expense').group_by(
        Accounts.date).order_by(Accounts.date).all())

    over_time_incomes = []
    over_time_expenses = []
    dates_label_inc = []
    dates_label_exp = []

    for amount, date in dates_income:
        dates_label_inc.append(date.strftime("%m-%d-%y"))
        over_time_incomes.append(float(amount))

    for amount, date in dates_expense:
        dates_label_exp.append(date.strftime("%m-%d-%y"))
        over_time_expenses.append(float(amount))

    # --- charts ---
    try:
        incomes_expense_chart = create_chart("Incomes to expenses ratio",
                                             data=[income_expense_ratio[0][0], income_expense_ratio[1][0]],
                                             background_col=['rgb(97, 75, 195)',
                                                             'rgb(51, 187, 197)'], labels=['Expense', 'Income'],
                                             chart_type_user='PIE')

        time_incomes_chart = create_chart("Incomes in a time period", data=over_time_incomes,
                                          background_col='rgb(97, 75, 195)', labels=dates_label_inc,
                                          chart_type_user='LINE', border_width=5, border_color='rgb(97, 75, 195)')
        time_expenses_chart = create_chart("Expenses in a time period", data=over_time_expenses,
                                           background_col='rgb(51, 187, 197)', labels=dates_label_exp,
                                           chart_type_user='LINE', border_width=5, border_color='rgb(51, 187, 197)')

        incomes_chart = create_chart("Incomes based on categories", data=[i[0] for i in incomes],
                                     background_col=generate_color(len(incomes)),
                                     labels=[i[1].capitalize() for i in incomes], chart_type_user='BAR')

        expenses_chart = create_chart("Expenses based on categories", data=[i[0] for i in expenses],
                                      background_col=generate_color(len(incomes)),
                                      labels=[i[1].capitalize() for i in expenses], chart_type_user='BAR')
    except IndexError:
        return render_template("error.html",
                               error='Not enough data to build your charts :(')

    chart1 = incomes_expense_chart.render()
    chart2 = time_incomes_chart.render()
    chart3 = time_expenses_chart.render()
    chart4 = incomes_chart.render()
    chart5 = expenses_chart.render()

    if current_user.id not in ai_cache:
        Thread(target=run_async_task, args=(
            current_user.id,
            income_expense_ratio[1][0],
            income_expense_ratio[0][0]
        )).start()

    return render_template("chart.html",
                           charts_html1=chart1,
                           charts_html2=chart2,
                           charts_html3=chart3,
                           charts_html4=chart4,
                           charts_html5=chart5,
                           ai_summary=ai_cache.get(current_user.id),
                           title='Dashboard', )

@app.route('/get_ai_summary')
@login_required
def get_ai_summary():
    return jsonify({"summary": ai_cache.get(current_user.id, "Summary is being generated...")})


@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    ai_cache.clear()
    form = AddAccountForm()
    if form.validate_on_submit():
        if datetime.date.today() < datetime.datetime.strptime(form.date.data.strftime('%Y-%m-%d'),
                                                              '%Y-%m-%d').date():
            flash("Your chosen date is in the future! Impossible to add an account on the day that hasn't come yet...",
                  'danger')
            return render_template('_base_form.html', title='Add an account', form=form)
        else:
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
            return redirect('/home')
    return render_template('_base_form.html', title='Add an account', form=form)


@app.route('/accounts/<int:_id>', methods=['GET', 'POST'])
@login_required
def edit_account(_id):
    ai_cache.clear()
    db_sess = db_session.create_session()
    account = db_sess.get(Accounts, _id)
    if account is None:
        abort(404)
    form = AddAccountForm()
    if request.method == "GET":
        form.type.data = account.type
        form.category.data = account.category
        form.date.data = account.date
        form.amount.data = account.amount
        return render_template('_base_form.html', title='Editing an account', form=form)
    if form.validate() and request.method == 'POST':
        account.type = form.type.data
        account.category = form.category.data
        account.date = form.date.data
        account.amount = form.amount.data
        db_sess.merge(account)
        db_sess.commit()
        flash("Account edited successfully!", 'success')
        return redirect('/home')


@app.route('/account_delete/<int:_id>')
@login_required
def account_delete(_id):
    ai_cache.clear()
    db_sess = db_session.create_session()
    account = db_sess.get(Accounts, _id)
    if account is None:
        abort(404)
    db_sess.delete(account)
    db_sess.commit()
    flash("Account deleted successfully!", 'success')
    return redirect('/home')


@login_manager.user_loader
def load_user(user_id: id) -> User | None:
    return db_session.create_session().get(User, user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    ai_cache.clear()
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash("Logged in successfully!", 'success')
            return redirect("/home")
        return render_template('_base_form.html',
                               message="Incorrect login credentials!",
                               title='Error while logging in',
                               form=form)
    return render_template('_base_form.html', title='Log in', form=form)


@app.route('/logout')
@login_required
def logout():
    ai_cache.clear()
    logout_user()
    flash("Logged out successfully", 'success')
    return redirect("/login")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        profile_picture_file = form.pfp.data

        picture_filename = 'default_pfp.png'
        if profile_picture_file:
            original_filename = secure_filename(profile_picture_file.filename)
            extension = os.path.splitext(original_filename)[1]
            picture_filename = f"user{db_sess.query(User).order_by(User.id.desc()).first().id}{extension}"
            picture_path = os.path.join(app.root_path, 'static', 'img', picture_filename)
            profile_picture_file.save(picture_path)

        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            email=form.email.data,
            pfp=picture_filename,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        flash("Registered successfully!", 'success')
        return redirect('/login')
    return render_template('_base_form.html', title='Sign up', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    if user is None:
        abort(404)
    form = RegisterForm()
    if request.method == "GET":
        form.surname.data = user.surname
        form.name.data = user.name
        form.age.data = user.age
        form.email.data = user.email
        return render_template('_base_form.html', title='Editing profile', form=form, pfp=user.pfp)
    if form.validate() and request.method == 'POST':
        profile_picture_file = form.pfp.data
        picture_filename = user.pfp if user.pfp else 'default_pfp.png'
        if profile_picture_file:
            original_filename = secure_filename(profile_picture_file.filename)
            extension = os.path.splitext(original_filename)[1]
            picture_filename = f"user{db_sess.query(User).order_by(User.id.desc()).first().id}{extension}"
            picture_path = os.path.join(app.root_path, 'static', 'img', picture_filename)
            profile_picture_file.save(picture_path)
        user.surname = form.surname.data
        user.name = form.name.data
        user.age = form.age.data
        user.email = form.email.data
        user.pfp = picture_filename
        user.set_password(form.password.data)
        db_sess.merge(user)
        db_sess.commit()
        db_sess.close()
        flash("Edited profile successfully!", 'success')
        return redirect('/profile')
    return render_template('_base_form.html', title='Editing profile', form=form, pfp=user.pfp)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    return render_template('profile.html', user=user, title='Your profile')


@app.route('/extra_login', methods=['GET', 'POST'])
def extra_login():
    form = ExtraLoginForm()
    if form.validate_on_submit():
        return redirect('/success')
    return render_template('_base_form.html', title='Emergency Access', form=form)


if __name__ == '__main__':
    db_session.global_init("db/database.sqlite")
    app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)
    app.run(port=8080, debug=True)

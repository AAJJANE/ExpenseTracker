import datetime
import json
from decimal import Decimal
from requests import get
from flask import Flask, render_template, request, redirect, abort, make_response, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from pychartjs.charts import Chart
from pychartjs.datasets import Dataset
from pychartjs.enums import ChartType
from pychartjs.options import ChartOptions, Legend, Title

from data import __db_session as db_session
from data.accounts import Accounts
from sqlalchemy import create_engine, Column, Integer, String, func
from forms import (LoginForm, ExtraLoginForm, RegisterForm)

from data.users import User
from forms.accountform import AddAccountForm
from utils import format_amount, create_chart, generate_color

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/home')
@login_required
def index():
    db_sess = db_session.create_session()
    accounts = db_sess.query(Accounts).filter(Accounts.user == current_user.id).order_by(Accounts.date.asc()).all()
    return render_template('index.html', title='Expenses', accounts=accounts)

@app.route('/')
def start():
    return render_template('unauthorized.html')

@app.errorhandler(401)
def unauthorized(error):
    return render_template('unauthorized.html')

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
                                                     'rgb(51, 187, 197)'],
                                     labels=['Expense', 'Income'],
                                     chart_type='PIE')

        time_incomes_chart = create_chart("Incomes in a time period",
                                          data=over_time_incomes,
                                          background_col='rgb(97, 75, 195)',
                                          labels=dates_label_inc,
                                          chart_type='LINE',
                                          border_color='rgb(97, 75, 195)',
                                          border_width=5)
        time_expenses_chart = create_chart("Expenses in a time period",
                                           data=over_time_expenses,
                                           background_col='rgb(51, 187, 197)',
                                           labels=dates_label_exp,
                                           chart_type='LINE',
                                           border_color='rgb(51, 187, 197)',
                                           border_width=5)

        incomes_chart = create_chart("Incomes based on categories",
                                     data=[i[0] for i in incomes],
                                     background_col=generate_color(len(incomes)),
                                     labels=[i[1].capitalize() for i in incomes],
                                     chart_type='BAR')

        expenses_chart = create_chart("Expenses based on categories",
                                      data=[i[0] for i in expenses],
                                      background_col=generate_color(len(incomes)),
                                      labels=[i[1].capitalize() for i in expenses],
                                      chart_type='BAR')
    except IndexError:
        return render_template("error.html",
                           error='Not enough data to build your charts :(')

    chart1 = incomes_expense_chart.render()
    chart2 = time_incomes_chart.render()
    chart3 = time_expenses_chart.render()
    chart4 = incomes_chart.render()
    chart5 = expenses_chart.render()

    return render_template("chart.html",
                           charts_html1=chart1,
                           charts_html2=chart2,
                           charts_html3=chart3,
                           charts_html4=chart4,
                           charts_html5=chart5,)


@app.route('/add_account', methods=['GET', 'POST'])
@login_required
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
        return redirect('/home')
    return render_template('_base_form.html', title='Add an account', form=form)

@app.route('/accounts/<int:_id>', methods=['GET', 'POST'])
@login_required
def edit_account(_id):
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
        return render_template('_base_form.html', title='Editing job', form=form)
    if form.validate() and request.method == 'POST':
        account.type = form.type.data
        account.category = form.category.data
        account.date = form.date.data
        account.amount = form.amount.data
        db_sess.merge(account)
        db_sess.commit()
        return redirect('/home')


@app.route('/account_delete/<int:_id>')
@login_required
def account_delete(_id):
    db_sess = db_session.create_session()
    account = db_sess.get(Accounts, _id)
    if account is None:
        abort(404)
    db_sess.delete(account)
    db_sess.commit()
    return redirect('/home')


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
            return redirect("/home")
        return render_template('_base_form.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('_base_form.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")


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

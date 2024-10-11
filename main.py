import sqlite3
import sendemailpy3 as smpy
import datetime
import schedule
import os
from gpa_calc import do_get
from flask import render_template, Flask, request
from flask.views import MethodView
from wtforms import Form, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired
import threading
import time

app = Flask(__name__)

connection = sqlite3.connect("students.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS students"
               "(username text, password text, date date, email text)")


def value_exists(username):
	connection = sqlite3.connect("students.db")
	cursor = connection.cursor()
	cursor.execute('SELECT 1 FROM students WHERE username = ?', (username,))
	connection.commit()
	return cursor.fetchone() is not None

def daily_check():
	connection = sqlite3.connect("students.db")
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM students")
	students = cursor.fetchall()
	for student in students:
		username = student[0]
		password = student[1]
		receiver_email = student[3]
		username_sender = os.getenv("USERNAME_SENDER")
		password_sender = os.getenv("PASSWORD_SENDER")
		subject = "Current Weighted and Unweighted GPA"
		body = do_get(username, password)
		date = student[2]
		if (datetime.date.today() - date).days == 0:
			smpy.send_gmail(subject, body, receiver_email, username_sender, password_sender)
	connection.commit()


def add_student(username, password, email):
	connection = sqlite3.connect("students.db")
	cursor = connection.cursor()
	cursor.execute(
	f"INSERT INTO students VALUES ('{username}', '{password}', '{datetime.date.today()}', '{email}')")
	connection.commit()


class UserForm(Form):
	username = StringField("Username:", validators=[DataRequired()])
	password = StringField("Password:", validators=[DataRequired()])
	email = StringField("Email:", validators=[DataRequired()])
	password_change = BooleanField("I want to change my password")
	submit = SubmitField("Submit")


class MainPage(MethodView):
	def get(self):
		user_form = UserForm()
		return render_template('index.html', user_form=user_form)
	def post(self):
		user_form = UserForm(request.form)
		username = str(user_form.username.data)
		password = str(user_form.password.data)
		email = str(user_form.email.data)
		password_change = bool(user_form.password_change.data)
		error_code = "Successfully registered"
		try:
			do_get(username, password)
			if not password_change and value_exists(username):
				raise KeyError
		except NameError:
			error_code = "User does not exist in HAC"
		except KeyError:
			error_code = "User already exists"
		except ValueError:
			error_code = "Please enter a value."
		except Exception as e:
			print(e)
			error_code = "An error occurred while signing up. Please try again."
		finally:
			add_student(username, password, email)
			return render_template("index.html", user_form=user_form, error_code=error_code)


connection.commit()

schedule.every().day.at("06:00").do(daily_check, cursor)


def run_schedule():
	while True:
		schedule.run_pending()
		time.sleep(60)


thread = threading.Thread(target=run_schedule)
thread.start()

connection.close()

if __name__ == "__main__":
	app.add_url_rule('/', view_func=MainPage.as_view('index'))
	app.run(debug=True)

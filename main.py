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


def adapt_date(date):
	return date.isoformat()


def convert_date(date_string):
	return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()


sqlite3.register_adapter(datetime.date, adapt_date)
sqlite3.register_converter("DATE", convert_date)


# Database setup
def get_db_connection():
	connection = sqlite3.connect("students.db")
	connection.row_factory = sqlite3.Row
	return connection


def create_students_table():
	with get_db_connection() as connection:
		cursor = connection.cursor()
		cursor.execute("CREATE TABLE IF NOT EXISTS students"
		               "(username text, password text, date date, email text)")
		connection.commit()

create_students_table()


def value_exists(username):
	with get_db_connection() as connection:
		cursor = connection.cursor()
		cursor.execute('SELECT 1 FROM students WHERE username = ?', (username,))
		return cursor.fetchone() is not None


def daily_check():
	with get_db_connection() as connection:
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM students")
		students = cursor.fetchall()
		for student in students:
			username = student['username']
			password = student['password']
			receiver_email = student['email']
			username_sender = os.getenv("USERNAME_SENDER")
			password_sender = os.getenv("PASSWORD_SENDER")
			subject = "Current Weighted and Unweighted GPA"
			body = do_get(username, password)
			date = datetime.datetime.strptime(student['date'], '%Y-%m-%d').date()
			if (datetime.date.today() - date).days == 0:
				smpy.send_gmail(subject, body, receiver_email, username_sender, password_sender)


def add_student(username, password, email):
	with get_db_connection() as connection:
		cursor = connection.cursor()
		cursor.execute(
			"INSERT INTO students (username, password, date, email) VALUES (?, ?, ?, ?)",
			(username, password, datetime.date.today(), email))
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
			add_student(username, password, email)
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
			return render_template("index.html", user_form=user_form, error_code=error_code)


schedule.every().day.at("06:00").do(daily_check)


def run_schedule():
	while True:
		schedule.run_pending()
		time.sleep(60)

# Start the scheduling in a separate thread
thread = threading.Thread(target=run_schedule, daemon=True)
thread.start()

if __name__ == "__main__":
	app.add_url_rule('/', view_func=MainPage.as_view('index'))
	app.run(debug=True)
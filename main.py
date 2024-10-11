import streamlit as st
import sqlite3
import sendemailpy3 as smpy
import datetime
import schedule
import os
import backend
from backend import do_get
import subprocess

st.title("GPA Calculator Server Signup")
connection = sqlite3.connect("students.db")
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS students"
               "(username int, password text, date date, email text)")


def value_exists(username):
	cursor.execute('SELECT 1 FROM students WHERE username = ?', (username,))
	return cursor.fetchone() is not None


with st.form("signup", clear_on_submit=True):
	username = st.text_input("Username", placeholder="Example: 287493")
	password = st.text_input("Password", type="password")
	email = st.text_input("Email", placeholder="Example: john.doe@example.com")
	password_change = st.checkbox("I want to change my password")
	submitted = st.form_submit_button("Submit")
	if submitted:
		try:
			if value_exists(username) and not(password_change):
				raise KeyError("Value already exists")
			if password == "" or username == "":
				raise ValueError("Please enter a value.")
			print(do_get(str(username), str(password)))
			cursor.execute(f"INSERT INTO students VALUES ('{username}', '{password}', '{datetime.date.today()}', '{email}')")
		except NameError:
			st.error("User does not exist in HAC")
		except KeyError:
			st.error("User already exists")
		except ValueError as e:
			print(e)
			st.error("Please enter a value.")
		# except Exception as e:
		# 	print(e)
		# 	st.error("An error occurred while signing up. Please try again.")
		else:
			st.success("Successfully registered")

def daily_check():
	cursor.execute("SELECT * FROM students")
	students = cursor.fetchall()
	for student in students:
		username = student[0]
		password = student[1]
		receiver_email = student[3]
		username_sender = os.getenv("USERNAME_SENDER")
		password_sender = os.getenv("PASSWORD_SENDER")
		subject = "Current Weighted and Unweighted GPA"
		body = backend.do_get(username, password)
		date = student[2]
		if (datetime.date.today() - date).days == 0:
			smpy.send_gmail(subject, body, receiver_email, username_sender, password_sender)


schedule.every().day.at("06:00").do(daily_check)

connection.commit()

connection.close()
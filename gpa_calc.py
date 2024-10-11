from bs4 import BeautifulSoup
from get_request_session import get_request_session


def do_get(username, password):
	try:
		session = get_request_session(username, password)
		courses_page_content = session.get(
			"https://hac.friscoisd.org/HomeAccess/Content/Student/Assignments.aspx").text

		parser = BeautifulSoup(courses_page_content, "lxml")

		grades = []
		names = []

		course_container = parser.find_all("div", "AssignmentClass")

		for container in course_container:
			new_course = {
				"name": "",
				"grade": "",
				"lastUpdated": "",
				"assignments": []
			}
			parser = BeautifulSoup(
				f"<html><body>{container}</body></html>", "lxml")
			header_container = parser.find_all(
				"div", "sg-header sg-header-square")
			assignements_container = parser.find_all("div", "sg-content-grid")

			for hc in header_container:
				parser = BeautifulSoup(
					f"<html><body>{hc}</body></html>", "lxml")

				new_course["name"] = parser.find(
					"a", "sg-header-heading").text.strip()

				new_course["grade"] = parser.find("span", "sg-header-heading sg-right").text.strip(
				).replace("Student Grades ", "").replace("%", "")

				names.append(new_course["name"])
				grades.append(new_course["grade"])

		weighted_list = []
		for i in range(len(names)):
			if grades[i] != "0.00" and grades[i] != "":
				if "AP" in names[i]:
					weighted_list.append(6.0)
					weighted_list.append(grades[i])
				elif "Adv" in names[i]:
					weighted_list.append(5.5)
					weighted_list.append(grades[i])
				else:
					weighted_list.append(5.0)
					weighted_list.append(grades[i])

		grades = [float(i) for i in grades if i != "0.00" and i != ""]

		unweighted_gpa_list = [(4.0 - ((100 - int(round(float(j)))) * 0.1)) for j in grades if j != ""]
		weighted_gpa_list = [float((weighted_list[k]) - (100 - int(round(float(weighted_list[k + 1])))) * 0.1) for k in
		                     range(0, len(weighted_list), 2)]
		unweighted_gpa = sum(unweighted_gpa_list) / len(unweighted_gpa_list)
		weighted_gpa = sum(weighted_gpa_list) / len(weighted_gpa_list)
		return f'''Unweighted GPA: {unweighted_gpa}\nWeighted GPA: {weighted_gpa}'''
	except ArithmeticError as e:
		print(e)
		raise NameError("Invalid username or password")
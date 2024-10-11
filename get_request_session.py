import requests
from bs4 import BeautifulSoup
import lxml

def get_request_session(username, password):
	request_session = requests.session()

	login_screen_response = request_session.get("https://hac.friscoisd.org/HomeAccess/Account/LogOn?ReturnUrl=%2fHomeAccess%2f").text

	parser =  BeautifulSoup(login_screen_response, "lxml")

	request_verification_token = parser.find('input', attrs={'name': '__RequestVerificationToken'})["value"]

	request_headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36',
		'X-Requested-With': 'XMLHttpRequest',
		'Host': 'hac.friscoisd.org',
		'Origin': 'hac.friscoisd.org',
		'Referer': "https://hac.friscoisd.org/HomeAccess/Account/LogOn?ReturnUrl=%2fhomeaccess%2f",
		'__RequestVerificationToken': request_verification_token
	}

	request_payload = {
		"__RequestVerificationToken" : request_verification_token,
		"SCKTY00328510CustomEnabled" : "False",
		"SCKTY00436568CustomEnabled" : "False",
		"Database" : "10",
		"VerificationOption" : "UsernamePassword",
		"LogOnDetails.UserName": username,
		"tempUN" : "",
		"tempPW" : "",
		"LogOnDetails.Password" : password
	}

	page_dom = request_session.post(
		"https://hac.friscoisd.org/HomeAccess/Account/LogOn?ReturnUrl=%2fHomeAccess%2f",
		data=request_payload,
		headers=request_headers
	)

	return request_session

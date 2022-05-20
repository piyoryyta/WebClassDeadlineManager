import requests
import re
from bs4 import BeautifulSoup
import traceback
import datetime
import time
import configparser
from pprint import pprint
ini = configparser.ConfigParser()
ini.read("./userConfig.ini", "UTF-8")

#ドメイン
domain_name = ini["Config"]["domainname"]
#ログイン情報
USER = ini["UserInfo"]["username"]
PASSWORD = ini["UserInfo"]["password"]
session = requests.session()

login_info = {
	"username" : USER,
	"val" : PASSWORD,
	"language" : "JAPANESE"
}

##ユーザー情報をセーブ
def setUserInfo(user=USER, password=PASSWORD, save=True):
	global login_info, USER, PASSWORD
	ini.set("UserInfo", "username", user)
	ini.set("UserInfo", "password", password)

	if(save):
		with open('userConfig.ini', 'w') as file:
			ini.write(file)

	login_info = {
		"username" : user,
		"val" : password,
		"language" : "JAPANESE"
	}
	USER = user
	PASSWORD = password

	print(login_info)


##ログイン後、コース一覧画面を取得
def login(domain_name = domain_name):
	login_info = {
		"username" : USER,
		"val" : PASSWORD,
		"language" : "JAPANESE"
	}
	print(login_info)
	print(PASSWORD)
	session.cookies.clear()
	url_login = domain_name + "/webclass/login.php"
	res = session.post(url_login, data=login_info, headers={"User-Agent":"WCDM Scraper(https://github.com/piyoryyta/)"})
	res.raise_for_status()
	if("もう一度お願いします" in res.text):
		raise ValueError("ユーザー情報が違います")
	return res

##全コースのURL取得
def get_course_list(res):
	#コースリストページ取得
	soup = BeautifulSoup(res.text,"html.parser")
	url_home = soup.select_one("script").string
	url_home = domain_name +  re.findall("\"(.*)\"", url_home)[0]

	res = session.post(url_home)
	res.raise_for_status()

	#全コースリスト取得
	soup = BeautifulSoup(res.text,"html.parser")
	courseTable = soup.select_one(".schedule-table tbody")
	course_list = []
	course_list.extend(courseTable.select("a"))
	course_list.extend(soup.select(".course-title a"))
	course_list = list(set(course_list))

	#全コースURL抽出
	for i in range(len(course_list)):
		course_list[i] = domain_name + course_list[i].attrs["href"]
	if(len(course_list)==0):
		raise Exception("コースがありません")

	return course_list

##コースの情報を取得
#{"courseName": "(コース名)", "contents": [{"title": "(レポート名)", "due": "(期限)"},..]}
def get_course_info(url):
	res = session.post(url)
	res.raise_for_status()
	soup = BeautifulSoup(res.text,"html.parser")
	course_url = soup.select_one("script").string
	course_url = domain_name +  re.findall("\"(.*)\"", course_url)[0]
	info = {"courseName": "", "contents": []}
	res = session.post(course_url)
	res.raise_for_status()
	soup = BeautifulSoup(res.text,"html.parser")

	info["courseName"] = soup.select_one(".course-name").get_text()
	course_items = soup.select(".cl-contentsList_content")
	contents = []
	for content_raw in course_items:
		content = {}
		if content_raw.select_one(".cm-contentsList_contentName a"):
			content["title"] = content_raw.select_one(".cm-contentsList_contentName a").get_text()
			content["type"] = content_raw.select_one(".cl-contentsList_categoryLabel").get_text()
			due_raw = content_raw.select_one(".cm-contentsList_contentDetailListItemData")
			# content["due"] = datetime.datetime.strptime(due_raw.get_text().split(" - ")[1], "%Y/%m/%d %H:%M")
			try:
				content["due"] = datetime.datetime.strptime(due_raw.get_text().split(" - ")[1], "%Y/%m/%d %H:%M")
				content["submitted"] = False
				contents.append(content)
			except:
				if content["type"]=="レポート":
					content["due"] = None
					content["submitted"] = False
					contents.append(content)
	info["contents"] = contents
	return info

#course_infoの配列を[{"courseName":"コース名","type": "種類", "title":"レポート名", "due":(期日)},...]にパースする
def parse_courses(course_info):
	contents = []
	for course in course_info:
		for content in course["contents"]:
			if (content["due"]!=None):
				due= content["due"].strftime("%Y/%m/%d %H:%M")
			else:
				due= "情報なし"
			contents.append({"courseName": course["courseName"], "type": content["type"], "title": content["title"], "due": due})
	return contents
if __name__ == "__main__":
	main()

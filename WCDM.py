import WebClassScraper as wc
import requests
import sys
import tkinter as tk
from tkinter import ttk
import time
import random
import schedule
import threading
import datetime
import configparser
import numpy as np
from plyer import notification
import pystray
from pystray import Icon
from PIL import Image
import webbrowser
from packaging import version

ini = configparser.ConfigParser()
ini.read("./userConfig.ini", "UTF-8")

ver = "v1.2"

def check_update():
	try:
		response = requests.get("https://api.github.com/repos/piyoryyta/WebClassDeadlineManager/releases/latest")
		if version.parse(response.json()["tag_name"]) > version.parse(ver):
			return response.json()["tag_name"]
	except:
		pass
	return None

##GUI Class
class GUI(tk.Frame):

	def __init__(self,master = None):

		def show_git():
			webbrowser.open("https://github.com/piyoryyta/WebClassDeadlineManager")
		def show_about():
			about_root = tk.Toplevel()
			about_root.geometry("400x70")
			about_root.resizable(False,False)
			about_root.grab_set()
			aboutLabel = tk.Label(about_root, text="WebClass非公式 期日管理システム "+ver+"\nby piyoryyta")
			aboutLabel.pack()
			sep = ttk.Separator(about_root)
			sep.pack(fill="both")
			aboutLabel2 = tk.Label(about_root, text="このプログラムを利用したことによって生じた不利益に対して、"+
													"\n製作者は一切の責任を負いません。")
			aboutLabel2.pack()

		super().__init__(master)
		self.master = master
		master.title(u"WebClass非公式 期日管理システム ver "+ver)
		master.geometry("1000x600")
		master.minsize(210,70)
		master.iconbitmap(default="./icon.ico")
		master.protocol("WM_DELETE_WINDOW", lambda:self.close())

		menuBar = tk.Menu(master)
		master.config(menu = menuBar)
		menu_file = tk.Menu(master)
		menuBar.add_cascade(label="ファイル", menu=menu_file)
		menu_file.add_command(label="コース情報更新(終わるまで止まります)", command=self.get_courses)
		menu_file.add_command(label="終了", command=master.quit)
		# menu_config = tk.Menu(master)
		# menu_config.add_command(label="", command=show_about)
		# menuBar.add_cascade(label="設定", menu=menu_config)
		menu_help = tk.Menu(master)
		menuBar.add_cascade(label="ヘルプ", menu=menu_help)
		menu_help.add_command(label="このプログラムについて", command=show_about)
		menu_help.add_command(label="配布ページへ(Github)", command=show_git)

		courseFrame = tk.Frame(master)
		courseFrame.place(rely=0.05, relwidth=1, relheight=0.85)

		self.sort="courseName"
		self.courseTree = ttk.Treeview(courseFrame, height = 40, columns = ("courseName", "type", "title", "reportDue"))
		self.courseTree.column('#0',width=0, stretch='no')
		self.courseTree.column('courseName',width=450)
		self.courseTree.column('type',width=50)
		self.courseTree.column('title',width=250)
		self.courseTree.column('reportDue',width=120)
		self.courseTree.heading("courseName", text="コース名", command= lambda: self.reloadTree(sort="courseName"))
		self.courseTree.heading("type", text="種類")
		self.courseTree.heading("title", text="名前")
		self.courseTree.heading("reportDue", text="期日", command= lambda: self.reloadTree(sort="due"))
		self.courseTree.pack(side="left")

		filterFrame = tk.Frame(courseFrame)
		filterFrame.pack(anchor=tk.NE)
		self.reportFilter = tk.BooleanVar()
		reportFilterCheck = tk.Checkbutton(filterFrame, variable=self.reportFilter, text="レポートをフィルター", command= lambda :self.reloadTree(mask=["レポート"]) if self.reportFilter.get()==True else self.reloadTree())
		reportFilterCheck.pack(anchor=tk.SW)

		self.dueFilter = tk.BooleanVar()
		dueFilterCheck = tk.Checkbutton(filterFrame, variable=self.dueFilter, text="期日でフィルター", command= lambda :self.reloadTree())
		dueFilterCheck.pack(anchor=tk.SW)

		statsFrame = tk.Frame(master)
		statsFrame.place(rely=0.9, relwidth=1, relheight=0.1)

		self.statsLabel = tk.Label(statsFrame)
		self.statsLabel.pack()
		self.statsLabel["text"] = "起動中..."

		self.statsProgress = ttk.Progressbar(statsFrame, length=400)
		self.statsProgress.pack()

		update = check_update()
		if update!=None:
			updateLabel = tk.Label(statsFrame, background='gray',foreground="white")
			updateLabel["text"] = "新しいバージョンがあります:"+update
			updateLabel.pack(anchor=tk.SE)

		if (ini["UserInfo"]["password"]=="" or ini["UserInfo"]["userName"]=="" ) and ini["Config"]["offline"]!="True":
			self.show_login()
		else:
			self.start_threads()

	def start_threads(self):
			schedule.every(30).minutes.do(self.get_courses)
			self.sc()
			self.reloadTree(sort="courseName")
			threading.Thread(target=self.first_get).start()

	def show_login(self):
		def login_proceed():
			ini["UserInfo"]["userName"]=usernameEntry.get()
			ini["UserInfo"]["password"]=passwordEntry.get()
			wc.setUserInfo(user=usernameEntry.get(), password=passwordEntry.get(), save=False)
			login_root.destroy()
			self.start_threads()
		def guest_login():
			ini["Config"]["offline"]="True"
			login_root.destroy()
			self.start_threads()

		login_root = tk.Toplevel()
		login_root.geometry("300x70")
		login_root.resizable(0,0)
		login_root.attributes('-toolwindow', True)
		login_root.attributes("-topmost", True)
		login_root.protocol("WM_DELETE_WINDOW", lambda:self.quit())

		usernameLabel = tk.Label(login_root,text="ユーザー名")
		usernameLabel.grid(row=0,column=0)
		usernameEntry = tk.Entry(login_root)
		usernameEntry.grid(row=0,column=1)
		usernameEntry.insert(tk.END, ini["UserInfo"]["userName"])

		passwordLabel = tk.Label(login_root,text="パスワード")
		passwordLabel.grid(row=1,column=0)
		passwordEntry = tk.Entry(login_root,show="●")
		passwordEntry.grid(row=1,column=1)
		passwordEntry.bind("<Return>", lambda event: login_proceed())

		proceesButton = tk.Button(login_root, text="ログイン", command=login_proceed)
		proceesButton.grid(row=2,column=1)
		guestButton = tk.Button(login_root, text="オフラインモード", command=guest_login)
		guestButton.grid(row=2,column=2)

	def sc(self):
		schedule.run_pending()
		self.after(3, self.sc)

	def close(self):
		if(ini["Config"]["trayOnExit"]=="True"):
			self.master.iconify()
			time.sleep(0.1)
			self.master.withdraw()
		else:
			quit()

	def show(self):
		self.master.deiconify()

	def first_get(self):
		self.get_courses(hideNoti=True)
		course = wc.parse_courses(self.course_info)
		self.getNearDeadline(course)

	def get_courses(self, hideNoti = False):
		if (ini["Config"]["offline"]=="True"):
			self.statsLabel["text"] = "オフラインモード"
			self.course_info = np.load("course.npy", allow_pickle=True)
			return
		self.dt_now = datetime.datetime.now()
		try:
			self.statsLabel["text"] = "ログイン中...(" + wc.USER + ")"
			listpage = (wc.login())
		except ValueError as e:
			print(e)
			self.statsLabel["text"] = "ログインに失敗しました"
			return
		except Exception as e:
			print(e)
			self.statsLabel["text"] = "エラーが発生しました(urlかネットワークを確認してください)"
			return
		time.sleep(1)
		self.statsLabel["text"] = "コースリスト取得中..."
		course_list = wc.get_course_list(listpage)
		time.sleep(1)
		self.statsLabel["text"] = "コース詳細取得中..."
		self.course_info = []
		self.statsProgress.configure(maximum=len(course_list))
		for i in range(len(course_list)):
			self.course_info.append(wc.get_course_info(course_list[i]))
			self.statsLabel["text"] = "コース詳細取得中...(" + str(i) + "/" + str(len(course_list)) +")"
			self.statsProgress.configure(value=i)
			time.sleep(1 + random.uniform(0,2)) #マナー
		self.statsProgress.configure(value=len(course_list))
		self.statsLabel["text"] = "コース情報更新完了(" + wc.USER  +")    最終更新:" + datetime.datetime.strftime(self.dt_now,"%Y/%m/%d %H:%M")
		self.reloadTree(self.course_info)

		courses = wc.parse_courses(self.course_info)
		try:
			old_course_info = np.load("course.npy", allow_pickle=True)
		except:
			old_course_info = []
		old_course_info = wc.parse_courses(old_course_info)
		new_report = []
		for report in courses:
			if not(report in old_course_info):
				new_report.append(report)
		self.getNearDeadline(new_report,show=not hideNoti)
		np.save("course.npy", self.course_info, allow_pickle=True)

	def reloadTree(self, course_info = None, sort=None, mask = None):
		if sort!=None:
			self.sort=sort
		for row in self.courseTree.get_children():
			self.courseTree.delete(row)
		try:
			if (course_info==None):
				course_info = np.load("course.npy", allow_pickle=True)
			iid=0
			course_info = wc.parse_courses(course_info)
			course_info.sort(key=lambda x:x[self.sort])
			for course in course_info:
				if ((self.dueFilter.get()==False) or self.isDeadlineNear(course)) and (mask==None or course["type"] in mask):
					self.courseTree.insert(parent="", index="end", iid=iid, value=(course["courseName"], course["type"], course["title"], course["due"]))
				iid+=1
		except Exception as e:
			print(str(sys.exc_info()[1]))
			for row in self.courseTree.get_children():
				self.courseTree.delete(row)

	def getNearDeadline(self,courses, show = True,days = int(ini["Config"]["deadlinedays"])):
		due_courses = []
		for course in courses:
				if(self.isDeadlineNear(course)):
					due_courses.append(course)
		if(due_courses!=[] and show):
			notification.notify(
				title="期日の近いレポートがあります",
				message=str(len(due_courses))+" 件のレポートが"+str(days)+"日以内に締切を迎えます",
				app_name="WebClass 非公式レポート管理システム",
				app_icon="./icon.ico",
				timeout=10
				)
		return due_courses

	def isDeadlineNear(self, course,now = datetime.datetime.now(),days = int(ini["Config"]["deadlinedays"])):
		try:
			due = datetime.datetime.strptime(course["due"],"%Y/%m/%d %H:%M")
			if(due-now<=datetime.timedelta(days=days)):
				return True
		except ValueError:
			pass
		return False

class Tray():
	def __init__(self,app = None):
		self.app = app

	def showIcon(self):
		threading.Thread(target=self.iconThread, daemon=True).start()
	def iconThread(self):
		menu = pystray.Menu(
				self.showmenu,
				self.quitmenu)
		iconImg = Image.open("icon.ico")
		self.icon = pystray.Icon("WCDMTray", iconImg, "WebClass 非公式レポート管理システム", menu)
		self.icon.run()

	def set_menu(self,callback):
		self.showmenu = pystray.MenuItem("Show", callback[0])
		self.quitmenu = pystray.MenuItem("Quit", callback[1])

class app():
	def __init__(self, window = None, tray = None):
		self.window = window
		self.tray = tray
		tray.set_menu([lambda : self.show(),lambda : self.close()])
		tray.showIcon()
	def close(self):
		self.window.quit()
		quit()
	def show(self):
		self.window.show()
	def mainloop(self):
		self.window.mainloop()

##main
def main():
	root= tk.Tk()
	window = GUI(master=root)
	tray = Tray(app = window)
	application = app(window, tray)
	application.mainloop()

if __name__=='__main__':
	main()
import WebClassScraper as wc
import sys
import tkinter as tk
from tkinter import ttk
import tqdm
import time
import random
import schedule
import threading
import datetime
import logging
from pprint import pprint
import configparser
import numpy as np
from plyer import notification
import pystray
from pystray import Icon
from PIL import Image

ini = configparser.ConfigParser()
ini.read("./userConfig.ini", "UTF-8")

version = "1.0"

##GUI Class
class GUI(tk.Frame):

	def __init__(self,master = None):

		def show_about():
			about_root = tk.Toplevel()
			about_root.geometry("400x70")
			about_root.resizable(False,False)
			about_root.grab_set()
			aboutLabel = tk.Label(about_root, text="WebClass非公式 期日管理システム ver "+version+"(2022/05/18)\nby piyoryyta")
			aboutLabel.pack()
			sep = ttk.Separator(about_root)
			sep.pack(fill="both")
			aboutLabel2 = tk.Label(about_root, text="このプログラムを利用したことによって生じた不利益に対して、"+
													"\n製作者は一切の責任を負いません。")
			aboutLabel2.pack()

		super().__init__(master)
		self.master = master
		master.title(u"WebClass非公式 期日管理システム ver "+version)
		master.geometry("1000x500")
		master.minsize(210,70)
		master.iconbitmap(default="./icon.ico")
		master.protocol("WM_DELETE_WINDOW", lambda:self.close())

		menuBar = tk.Menu(master)
		master.config(menu = menuBar)
		menu_file = tk.Menu(master)
		menuBar.add_cascade(label="ファイル", menu=menu_file)
		menu_file.add_command(label="コース情報更新(終わるまで止まります)", command=self.get_courses)
		menu_file.add_command(label="終了", command=master.quit)
		menu_config = tk.Menu(master)
		menu_config.add_command(label="このプログラムについて", command=show_about)
		menuBar.add_cascade(label="設定", menu=menu_config)
		menu_help = tk.Menu(master)
		menuBar.add_cascade(label="ヘルプ", menu=menu_config)
		menu_help.add_command(label="このプログラムについて", command=show_about)
		menu_help.add_command(label="配布ページへ(Github)", command=show_about)

		courseFrame = tk.Frame(master)
		courseFrame.place(rely=0.05, relwidth=1, relheight=0.85)

		self.courseTree = ttk.Treeview(courseFrame, height = 40, columns = ("courseName", "type", "title", "reportDue"))
		self.courseTree.column('#0',width=0, stretch='no')
		self.courseTree.column('courseName',width=450)
		self.courseTree.column('type',width=50)
		self.courseTree.column('title',width=250)
		self.courseTree.column('reportDue',width=120)
		self.courseTree.heading("courseName", text="コース名", command=self.reloadTreebyName)
		self.courseTree.heading("type", text="種類")
		self.courseTree.heading("title", text="名前")
		self.courseTree.heading("reportDue", text="期日", command=self.reloadTreebyDue)
		self.courseTree.pack(side="left")

		statsFrame = tk.Frame(master)
		statsFrame.place(rely=0.9, relwidth=1, relheight=0.1)

		self.statsLabel = tk.Label(statsFrame)
		self.statsLabel.pack()
		self.statsLabel["text"] = "起動中..."

		self.statsProgress = ttk.Progressbar(statsFrame, length=400)
		self.statsProgress.pack()


		schedule.every(30).minutes.do(self.get_courses)
		self.sc()
		self.reloadTree()
		threading.Thread(target=self.first_get).start()

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

	def reloadTree(self, course_info = None, sort="courseName"):
		for row in self.courseTree.get_children():
			self.courseTree.delete(row)
		try:
			if (course_info==None):
				course_info = np.load("course.npy", allow_pickle=True)
			iid=0
			course_info = wc.parse_courses(course_info)
			course_info.sort(key=lambda x:x[sort])
			for course in course_info:
					self.courseTree.insert(parent="", index="end", iid=iid, value=(course["courseName"], course["type"], course["title"], course["due"]))
					iid+=1
		except Exception as e:
			print(str(sys.exc_info()[1]))
			for row in self.courseTree.get_children():
				self.courseTree.delete(row)
	def reloadTreebyName(self):
		self.reloadTree(sort="courseName")
	def reloadTreebyDue(self):
		self.reloadTree(sort="due")

	def getNearDeadline(self,courses,now=datetime.datetime.now(),days=int(ini["Config"]["deadlinedays"]), show=True):
		due_courses = []
		for course in courses:
			try:
				due = datetime.datetime.strptime(course["due"],"%Y/%m/%d %H:%M")
				if(due-now<=datetime.timedelta(days=days)):
					due_courses.append(course)
			except ValueError:
				pass
		if(due_courses!=[] and show):
			notification.notify(
				title="期日の近いレポートがあります",
				message=str(len(due_courses))+" 件のレポートが"+str(days)+"日以内に締切を迎えます",
				app_name="WebClass 非公式レポート管理システム",
				app_icon="./icon.ico",
				timeout=10
				)
		return due_courses

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
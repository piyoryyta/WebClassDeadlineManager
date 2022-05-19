# WebClassDeadlineManager
 WebClassDeadlineManager(WCDM)は、WebClass(授業支援システム)の**非公式**期日管理ツールです。
## 何ができるの?
 - 期日付きのコンテンツの管理
 - 期日の近いレポートの通知
 - (追加予定)期日の近いレポートをフィルター
## どうやって使うの?
1. userConfig.iniを設定します
2. WCDMを起動します
3. 自動でコース情報の更新が始まります
4. ツールを終了する際には画面上部のメニューから「ファイル->終了」もしくはタスクトレイのアイコンを右クリックして「Quit」を選択してください
## userConfig.iniについて
- **username**(文字列):ユーザー名
- **password**(文字列):パスワード
	- パスワードを平文で保存するので、個人の責任で入力してください
	- **現在、パスワードを保存せずに利用するシステムを製作中です**
- **domainname**(URL):利用するWebClassのドメイン名です
- **deadlinedays**(数字):何日前の期日まで通知するかを指定します
- **trayOnExit**(True/False):Trueの場合、閉じるボタンを押した際に、タスクトレイに最小化します
- **offline**(True/False):Trueの場合、WebClassに接続せず、最後に取得したコース情報を利用します

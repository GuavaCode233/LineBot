from __future__ import unicode_literals
import json
import datetime as dt
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import configparser

# initailize
app = Flask(__name__)
# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

# global variables
Running_daily = False

# bot functions
def update_daily():     # 更新每日 統測TCTE 學測GSAT
    with open("daily.json","r",encoding= "utf-8") as daily_file:
        Dailydata = json.load(daily_file)
    with open("daily.json","w",encoding="utf-8") as write_file:
        # get data
        List = Dailydata["list"].copy()
        # update
        today = List.pop(0)
        List.append(today)
        new_data = {"date":str(dt.datetime.now().day),"today":today,"list":List}
        Dailydata.update(new_data)
        json.dump(Dailydata, write_file, ensure_ascii=False)

def daily_report():
    with open("daily.json","r",encoding= "utf-8") as daily_file:
        Dailydata = json.load(daily_file)
    # get data
    today = Dailydata["today"]
    Date = dt.datetime.today().date()# 今天
    TCTE = dt.datetime.strptime(Dailydata["TCTE"], "%Y-%m-%d").date()
    GSAT = dt.datetime.strptime(Dailydata["GSAT"], "%Y-%m-%d").date()
    TCTE_day = (TCTE - Date).days
    GSAT_day = (GSAT - Date).days
    time = dt.datetime.now()
    return f"313班 {time.month}月{time.day}日 日報:\n今日值日生: {today[0]} 號、{today[1]} 號\n還不給我去幹活 笑你\n\n統測倒數: {TCTE_day} 天\n學測倒數: {GSAT_day} 天\n加油啊各位!!!"

# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        # print(body, signature)
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def Message(event):
    global Running_daily
    with open("daily.json","r",encoding= "utf-8") as daily_file:
        Dailydata = json.load(daily_file)
    if(event.message.text == ";run"): # 執行每日
        if(Running_daily):
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text = "Already running"))
            return
        else:
            Running_daily = True
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text = "Running"))
            while(Running_daily):
                time = dt.datetime.now()
                if(str(time.day) != Dailydata["date"] and time.hour >= 7): # 改日期了
                    Group_ID = Dailydata["Group_ID"]
                    update_daily()
                    line_bot_api.push_message(Group_ID,TextSendMessage(text=daily_report()))
                    with open("daily.json","r",encoding= "utf-8") as daily_file:
                        Dailydata = json.load(daily_file)

    elif(event.message.text == "get_group_id"): # 取得Group ID
        Group_ID = event.source.group_id
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text = f"Group ID: {event.source.group_id} Saved!"))
        print(event.source.group_id)
        with open("daily.json","w",encoding="utf-8") as write_file:
            new_data = {"Group_ID":Group_ID}
            Dailydata.update(new_data)
            json.dump(Dailydata, write_file, ensure_ascii=False)
    elif(event.message.text == "今日報告"):
        Group_ID = Dailydata["Test_ID"]
        line_bot_api.push_message(Group_ID,TextSendMessage(text=daily_report()))
    elif(event.message.text == ";stop"):
        Running_daily = False
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text = "Stopped"))
    elif(event.message.text == "add joke"): # 加笑話
        pass


if __name__ == "__main__":
    app.run()

import datetime
import os
from urllib import request
import json
import requests
from config import Config
import time
import smtplib
from email.mime.text import MIMEText
from flask import Blueprint

MineWorkorders = Blueprint('MineWorkorder', __name__)

OrderProcesses = Blueprint('OrderProcess', __name__)

OrderHistories = Blueprint('OrderHistory', __name__)


def send_mail(content, receiverMail):
    # 发送者邮箱地址
    senderMail = '**********@**.com'
    # 发送者邮箱授权码
    authcode = '*********'

    # 邮箱主题
    subject = 'DBAdmin通知！'

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['subject'] = subject
    msg['From'] = senderMail
    msg['To'] = receiverMail

    try:
        server = smtplib.SMTP_SSL('smtp.qq.com', smtplib.SMTP_SSL_PORT)
        print('成功连接到邮件服务器')
        server.login(senderMail, authcode)
        print('成功登录邮箱')
        server.sendmail(senderMail, receiverMail, msg.as_string())
        print('邮件发送成功')

    except smtplib.SMTPException as e:
        print('邮件发送异常')

    finally:
        server.quit()






def getToken():
    url = 'https://oapi.dingtalk.com/gettoken?appkey=' + Config.appkey + '&appsecret=' + Config.appsecret
    response = requests.get(url=url)
    result = response.json()
    errmsg = result['errmsg']
    print('获取密钥是否成功：', errmsg)
    try:
        access_token = result['access_token']
    except Exception as e:
        print(e)
        access_token = ''

    return access_token


def send_dingding(content, receive_user):
    access_token = getToken()

    # content = '这是一条测试信息！请忽略！'

    # 给用户发送工作通知
    url = 'https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2?access_token=' + access_token
    _data = {
        'agent_id': 1592905030,
        'userid_list': receive_user,
        'msg': {
            'msgtype': 'text',
            'text': {'content': content}}
    }
    data = json.dumps(_data)
    response = requests.post(url=url, data=data)
    result = response.json()
    print(result)

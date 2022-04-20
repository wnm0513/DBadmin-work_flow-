import datetime
import os
from urllib import request
import json
import time
import smtplib
from email.mime.text import MIMEText
from flask import Blueprint

MineWorkorders = Blueprint('MineWorkorder', __name__)

OrderProcesses = Blueprint('OrderProcess', __name__)

OrderHistories = Blueprint('OrderHistory', __name__)


def send_mail(content, receiverMail):
    # 发送者邮箱地址
    senderMail = '907209574@qq.com'
    # 发送者邮箱授权码
    authcode = 'ykczgqfcnggsbffa'

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



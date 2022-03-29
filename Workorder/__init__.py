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


def get_token():
    """#获取access_token"""
    tokenfile = './do_not_change_this_dingfile'
    expires_in = 3600
    CROPID = 'dingrhiiq5w6sbza5udq'
    SECRET = '9M9gECekk-aHMve64lRhxiP7iJlv3oPk0Epm7IUb7ua8cSIsg_rEALHA9sw6Ql-8'
    url = 'https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s' % (CROPID, SECRET)
    if os.path.exists(tokenfile):
        token_createtime = int(os.path.getctime(tokenfile))
        nowtime = int(time.time())
        # 如果key没有过期
        if nowtime - token_createtime < expires_in:
            file_token = open(tokenfile, 'r').readlines()
            token = file_token[0].replace('\n', '')
            return token
        else:
            req = request.Request(url)
            result = request.urlopen(req)
            access_token = json.loads(result.read())
            # 判断是返回了合法的值
            if access_token.has_key('errcode') and access_token['errcode'] == 0:
                # 将tocken持久化
                with open(tokenfile, 'w') as token:
                    token.write(access_token['access_token'])
                return access_token['access_token']
            else:
                print("get token error!")
                return ''
    else:
        req = request.Request(url)
        result = request.urlopen(req)
        access_token = json.loads(result.read())
        # 判断是返回了合法的值
        if access_token.has_key('errcode') and access_token['errcode'] == 0:
            # 将tocken持久化
            with open(tokenfile, 'w') as token:
                token.write(access_token['access_token'])
            return access_token['access_token']
        else:
            print("get token error!")
            return ''


def send_dingding(msg, receiveuser):
    ## 钉钉发消息 ##
    access_token = get_token()
    msg_type = 'text'
    url = "https://oapi.dingtalk.com/message/send?access_token=%s" % access_token
    to_users = '|'.join(receiveuser)
    body_dict = {"touser": to_users, "agentid": 204030964, "msgtype": msg_type, msg_type: {"content": msg}}
    body = json.dumps(body_dict)
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    requests = request.Request(url=url, headers=headers, data=bytes(body))
    response = request.urlopen(requests)
    resp = response.read()
    return_json = json.loads(resp)
    # 判断是返回了合法的值
    if return_json.has_key('errcode') and return_json['errcode'] == 0:
        print("send message successful!", return_json)
    else:
        print("send message failure!", return_json)
        error_msg = "===*=发送审批消息失败\n===*=消息内容\n\n{msg}\n\n===*=时间：{time}".format(msg=msg,
                                                                                 time=datetime.datetime.now().strftime(
                                                                                     '%Y-%m-%d %H:%M:%S'))
        return error_msg


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

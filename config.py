import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = 'dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://flask:@/flask?charset=utf8"
    MYSQLUSER = 'dbadmin'
    MYSQLPASSWORD = ''
    DB = 'flask'
    IP = ''
    PORT = '3306'
    # goinception本地账号
    INCEPTION_HOST = ''
    INCEPTION_PORT = '4000'
    INCEPTION_USER = 'goinception'
    INCEPTION_PASSWORD = ''
    # goinception备份信息
    INCEPTION_BACKUP_HOST = ''
    INCEPTION_BACKUP_PORT = '3306'
    INCEPTION_BACKUP_USER = 'dbadmin_backup'
    INCEPTION_BACKUP_PASSWORD = ''
    # 文件路径
    INCEPTION_PATH = os.path.join(basedir, 'File')
    INCEPTION_UPATH = os.path.join(basedir, 'static/img/userprofile/')
    # 上传文件限制
    UPLOADED_PROFILE_ALLOW = ['png', 'jpg', 'jpeg']
    # 网站ip
    WEB_IP = 'http://dbadmin-pre-new.banksteeltech.com'
    # dingding应用的参数
    appkey = ''
    appsecret = ''


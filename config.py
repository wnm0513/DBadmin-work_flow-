import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = 'dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://flask:Mysql$123@192.168.201.15/flask?charset=utf8"
    MYSQLUSER = 'root'
    MYSQLPASSWORD = 'Mysql@123'
    DB = 'flask'
    IP = '192.168.201.15'
    PORT = '3306'
    # goinception本地账号
    INCEPTION_HOST = '192.168.201.15'
    INCEPTION_PORT = '4000'
    INCEPTION_USER = 'goinception'
    INCEPTION_PASSWORD = 'Mysql$123'
    # goinception备份信息
    INCEPTION_BACKUP_HOST = '192.168.201.15'
    INCEPTION_BACKUP_PORT = '3306'
    INCEPTION_BACKUP_USER = 'dbadmin'
    INCEPTION_BACKUP_PASSWORD = 'Mysql$123'
    # 文件路径
    INCEPTION_PATH = os.path.join(basedir, 'File')
    INCEPTION_WPATH = os.path.join(basedir, 'WorkOrder')

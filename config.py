class Config(object):
    SECRET_KEY = 'dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://flask:Mysql$123@192.168.201.15/flask?charset=utf8"

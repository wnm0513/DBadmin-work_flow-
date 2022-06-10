import functools

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy import and_

import useddb
import pymysql
from flask_login import current_user
from useddb.models import db, User, Workorder
from config import Config
from login_required import login_required

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# 在加载页面时读取用户
@app.before_request
def load_logged_in_user():
    # 这里的user_id是在登录视图中赋值的
    user_id = session.get('user_id')
    # 下面就是做个判断并给全局变量g.user赋值
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.filter(User.id == user_id).first()
        # 查询工单，并以权限分类用户能看到的正在进行的工单
        if g.user.is_super():
            workorders = Workorder.query.filter(Workorder.status == 0).all()
        elif g.user.is_manager():
            workorders = db.session.query(Workorder).filter(
                and_(Workorder.deptid == g.user.deptId, Workorder.status == 0)).all()
        else:
            workorders = db.session.query(Workorder).filter(
                and_(Workorder.uid == g.user.id, Workorder.status == 0)).all()

        g.order_count = len(workorders)


@app.route('/index')
@login_required
def index():  # put application's code here
    return render_template('base.html')


# 注册蓝图到App
## 登录 ##
from Logins.login import Login

app.register_blueprint(Login, url_prefix='/')

## 首页 ##
# 修改用户信息
from index.AlterUser import Index_AlterUser

app.register_blueprint(Index_AlterUser, url_prefix='/AlterUserinfo')

## 工单管理 ##
# 我的工单
from Workorder.MineWorkorder import MineWorkorders

app.register_blueprint(MineWorkorders, url_prefix='/MineWorkorder')

# 工单进度
from Workorder.OderProcess import OrderProcesses

app.register_blueprint(OrderProcesses, url_prefix='/OrderProcess')

# 历史工单
from Workorder.OrderHistory import OrderHistories

app.register_blueprint(OrderHistories, url_prefix='/OrderHistory')

## 用户管理 ##
# 所有用户
from User.AllUser import AllUsers

app.register_blueprint(AllUsers, url_prefix='/AllUser')

# 部门管理
from User.Department import Departments_view

app.register_blueprint(Departments_view, url_prefix='/Department')

## 权限管理 ##
# 部门数据库
from DBs.DeptDB import DeptDBs

app.register_blueprint(DeptDBs, url_prefix='/DeptDB')

# 数据库权限管理
from DBs.AllDB import AllDBs

app.register_blueprint(AllDBs, url_prefix='/AllDBs')

## SQL执行 ##
# SQL执行
from SQL.sql_execute import sqlExecutes

app.register_blueprint(sqlExecutes, url_prefix='/sqlExecute')

# 历史SQL
from SQL.sql_history import sqlHistories

app.register_blueprint(sqlHistories, url_prefix='/sqlHistory')

# if __name__ == '__main__':
#    app.run(host="0.0.0.0", port=2022)

from gevent import pywsgi

if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 2022), app)
    server.serve_forever()
import functools

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import useddb
import pymysql
from flask_login import current_user
from useddb.models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# 在其他视图中验证
# 用户登录以后才能进行功能的使用。
# 在每个视图中可以使用 装饰器 来完成这个工作
def login_required(view):
    # 装饰器返回一个新的视图，该视图包含了传递给装饰器的原视图
    @functools.wraps(view)
    # 新的函数检查用户是否载入。
    # 如果已载入，那么就继续正常执行原视图
    def wrapped_view(**kwargs):
        # 否则就重定向到登录页面
        if g.user is None:
            return redirect(url_for('login.login'))

        return view(**kwargs)

    return wrapped_view


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


@app.route('/index')
@login_required
def index():  # put application's code here
    return render_template('base.html')


# 注册蓝图到App
## 登录 ##
from Logins.login import Login

app.register_blueprint(Login, url_prefix='/')

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="2022")

import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib
import useddb
import pymysql
from app import login_required
from useddb.models import db, User, UsersRoles, Departments, QueryHistory, Dbs, DbsDept
from . import sqlHistories


## 用户管理 ##
@sqlHistories.route('/sqlExecute', methods=['GET', 'POST'])
@login_required
def sqlHistory():
    # 根据用户权限选择可选择查询的数据库
    if g.user.is_super():
        queryhistory = QueryHistory.query.all()
    else:
        queryhistory = QueryHistory.query.filter_by(uid=g.user.id).all()

    return render_template('SQL/History/sqlHistory.html', queryhistory=queryhistory)

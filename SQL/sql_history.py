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
        dbs = []
        mydept_dbs = db.session.query(Dbs.name) \
            .join(DbsDept, DbsDept.dbid == Dbs.id) \
            .join(Departments, Departments.id == DbsDept.deptid) \
            .join(User, User.deptId == Departments.id) \
            .filter(User.id == g.user.id).all()
        for mydept_db in mydept_dbs:
            deptdbs = db.session.query(Dbs.ip, Dbs.name).group_by(Dbs.ip).filter(Dbs.name == mydept_db[0]).first()
            mydeptdblist = {
                'name': deptdbs.name
            }
            dbs.append(mydeptdblist)
        queryhistory = []
        for dept_db in dbs:
            mydepthistory = QueryHistory.query.filter(QueryHistory.dbname == dept_db['name']).first()
            queryhistory.append(mydepthistory)

    return render_template('SQL/History/sqlHistory.html', queryhistory=queryhistory)

import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib

from sqlalchemy import distinct, and_

import useddb
import pymysql
from app import login_required
from useddb.models import db, User, UsersRoles, Departments, Dbs, PrivilegesUsersDbs, Privilege
from . import PriDBs


## 用户权限管理 ##
@PriDBs.route('/PriDB', methods=['GET', 'POST'])
@login_required
def PriDB():
    users = db.session.query(User.id, User.name, User.account).all()
    users_prinfo = []
    for user in users:
        prdbcuont = db.session.query(Dbs.name.distinct()) \
            .join(PrivilegesUsersDbs, PrivilegesUsersDbs.uid == Dbs.id) \
            .filter(PrivilegesUsersDbs.uid == User.id).count()
        user_prinfo = {
            "name": user.name,
            "account": user.account,
            "prdbcount": prdbcuont
        }
        users_prinfo.append(user_prinfo)

    return render_template('DBs/PriDB/PriDB.html', users_prinfo=users_prinfo)


##
# 编辑用户权限 ##
@PriDBs.route('/PriEdit/<account>/', methods=['GET', 'POST'])
@login_required
def PriEdit(account):
    # 获取用户信息
    global dbname_id
    user = User.query.filter_by(account=account).first()
    # 获取与该用户相关的权限和数据库
    dbids = PrivilegesUsersDbs.query(distinct(PrivilegesUsersDbs.dbid)).filter_by(uid=user.id).all()
    # 从网页取值
    if request.method == 'POST':
        dbname = request.form.get('dbname')
        dbname_id = Dbs.query(Dbs.id).filter(Dbs.name == dbname).first()
    # 以获取的数据库id和用户id查找权限id
    for dbid in dbids:
        # 对比获取的数据库id和选中的数据库id，并查询权限
        if dbid == dbname_id:
            prsid = PrivilegesUsersDbs.query(PrivilegesUsersDbs.prid).filter(and_(dbid=dbid.id, uid=user.id)).all()

    dbs = Dbs.query.all()

    return render_template('DBs/PriDB/PriEdit.html', dbs=dbs, user=user)


## 添加用户权限 ##
@PriDBs.route('/PriDetail/<account>/', methods=['GET', 'POST'])
@login_required
def PriAdd(account):
    # 获取用户信息
    user = User.query.filter_by(account=account).first()
    # 确认更改
    if request.method == 'POST':
        name = request.form.get('name')
        account = request.form.get('account')
        passwd = request.form.get('password')
        dingding = request.form.get('dingding')
        phone = request.form.get('phone')
        email = request.form.get('email')

        m1 = hashlib.md5()
        m1.update(passwd.encode("utf8"))
        pwd_md5 = m1.hexdigest()

        user.name = name
        user.account = account
        user.ding = dingding
        user.phone = phone
        user.email = email
        user.pwd = pwd_md5

        # 提交信息
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            flash(e)
            return redirect(url_for('AllUser.Alluser'))

    return render_template('DBs/PriDB/PriAdd.html', user=user)


## 删除用户权限 ##
@PriDBs.route('/delete/<account>/', methods=['GET', 'POST'])
@login_required
def delete(account):
    user = User.query.filter_by(account=account).first()
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('PriDB.PriDB'))

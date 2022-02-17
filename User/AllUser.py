from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib
import useddb
import pymysql
from app import login_required
from useddb.models import db, User, UsersRoles, Departments
from . import AllUsers


# 用户管理
@AllUsers.route('/AllUser')
@login_required
def AllUser():
    # 连接查询
    users = db.session.query(User.account, User.name, User.email, User.phone, User.issuper,
                             User.ismanager, User.ctime, User.utime, User.role_name,
                             User.last_login, Departments.deptname).join(Departments,
                                                                         Departments.id == User.deptId)
    return render_template('Usermanage/AllUser.html', users=users)


# 新增用户
@AllUsers.route('/AddUser', methods=['GET', 'POST'])
@login_required
def AddUser():
    # 从网页取值
    if request.method == 'POST':
        name = request.form.get('name')
        account = request.form.get('account')
        dingding = request.form.get('dingding')
        phone = request.form.get('phone')
        email = request.form.get('email')
        passwd = request.form.get('password')
        role_name = request.form.get('role_name')
        deptname = request.form.get('deptId')
        # 判断check box是否被选中
        if request.form.get('ismanager'):
            ismanager = 1

        else:

            ismanager = 0

        if request.form.get('issuper'):
            issuper = 1

        else:

            issuper = 0

        m1 = hashlib.md5()
        m1.update(passwd.encode("utf8"))
        pwd_md5 = m1.hexdigest()
        deptId1 = Departments.query.filter(Departments.deptname == deptname).first()
        deptId = deptId1.id
        user = User(name=name, account=account, ding=dingding, passwd=pwd_md5, phone=phone, email=email,
                    role_name=role_name,
                    deptId=deptId, ismanager=ismanager, issuper=issuper)
        user1 = User.query.filter(User.name == name and User.account == account).first()
        if user1:
            error = 'already registered.'

        else:
            try:
                db.session.add(user)
                db.session.commit()
                error = 'registered successfully.'
            except db.IntegrityError:
                error = 'adding error!!!'

        flash(error)

    role_name = UsersRoles.query.all()
    department = Departments.query.all()

    return render_template('Usermanage/AddUser.html', role_name=role_name, department=department)


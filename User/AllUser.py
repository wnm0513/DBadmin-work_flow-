import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib
import useddb
import pymysql
from login_required import login_required
from useddb.models import db, User, UsersRoles, Departments
from . import AllUsers


## 用户管理 ##
@AllUsers.route('/AllUser', methods=['GET', 'POST'])
@login_required
def AllUser():
    users = []
    # 连接查询
    user = User.query.all()
    for u in user:
        dept = Departments.query.filter_by(id=u.deptId).first()
        if dept:
            user_info = {
                'name': u.name,
                'account': u.account,
                'role_name': u.role_name,
                'ding': u.ding,
                'phone': u.phone,
                'email': u.email,
                'ctime': u.ctime,
                'last_login': u.last_login,
                'ismanager': u.ismanager,
                'status': u.status,
                'deptname': dept.deptname
            }
            users.append(user_info)
        else:
            user_info = {
                'name': u.name,
                'account': u.account,
                'role_name': u.role_name,
                'ding': u.ding,
                'phone': u.phone,
                'email': u.email,
                'ctime': u.ctime,
                'last_login': u.last_login,
                'ismanager': u.ismanager,
                'status': u.status,
            }
            users.append(user_info)

    return render_template('Usermanage/AllUser/AllUser.html', users=users)


## 新增用户 ##
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
            except Exception as e:
                error = str(e)

        flash(error)

    role_name = UsersRoles.query.all()
    department = Departments.query.all()

    return render_template('Usermanage/AllUser/AddUser.html', role_name=role_name, department=department)


## 编辑用户信息 ##
@AllUsers.route('/UserEdit/<account>/', methods=['GET', 'POST'])
@login_required
def UserEdit(account):
    # 获取用户信息
    user = User.query.filter_by(account=account).first()
    dept = Departments.query.filter_by(id=user.deptId).first()
    department = Departments.query.all()
    # 确认更改
    if request.method == 'POST':
        name = request.form.get('name')
        account = request.form.get('account')
        passwd = request.form.get('password')
        dingding = request.form.get('dingding')
        phone = request.form.get('phone')
        email = request.form.get('email')
        deptname = request.form.get('deptId')


        m1 = hashlib.md5()
        m1.update(passwd.encode("utf8"))
        pwd_md5 = m1.hexdigest()
        deptId1 = Departments.query.filter(Departments.deptname == deptname).first()
        deptId = deptId1.id

        user.name = name
        user.account = account
        user.ding = dingding
        user.phone = phone
        user.email = email
        user.pwd = pwd_md5
        user.deptId =deptId
        # 判断check box是否被选中
        if request.form.get('ismanager'):
            user.ismanager = 1

        else:
            user.ismanager = 0

        # 提交信息
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            flash(e)

        return redirect(url_for('AllUser.AllUser'))


    return render_template('Usermanage/AllUser/UserEdit.html', user=user, dept=dept, department=department)


## 删除用户 ##
@AllUsers.route('/delete/<account>/', methods=['GET', 'POST'])
@login_required
def delete(account):
    user = User.query.filter_by(account=account).first()
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('AllUser.AllUser'))


## 改变用户状态 ##
@AllUsers.route('/change_status/<account>/', methods=['GET', 'POST'])
@login_required
def change_status(account):
    user = User.query.filter(User.account == account).first()
    if user.status == 0:
        user.status = 1

    else:
        user.status = 0

    # 更新修改时间
    user.utime = datetime.datetime.now()
    db.session.add(user)
    db.session.commit()

    return redirect(url_for('AllUser.AllUser'))

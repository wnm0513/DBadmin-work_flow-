from flask import (
    g, render_template, request, flash, redirect, url_for
)
from sqlalchemy import and_, func

from app import login_required
from useddb.models import db, User, Departments, Dbs, DbsDept, DbsUser
from . import AllDBs


@AllDBs.route('/AllDB', methods=['GET', 'POST'])
@login_required
def AllDB():
    dbs = db.session.query(
        Dbs.id,
        Dbs.name,
        Dbs.ip,
        Dbs.port,
        Dbs.note,
        func.group_concat(Departments.deptname),
        func.group_concat(User.name)
    ).outerjoin(DbsDept, DbsDept.dbid == Dbs.id) \
        .outerjoin(Departments, Departments.id == DbsDept.deptid)\
        .outerjoin(DbsUser, DbsUser.dbid == Dbs.id)\
        .outerjoin(User, User.id == DbsUser.uid)\
        .group_by(Dbs.id).order_by(Dbs.name.desc())

    return render_template('DBs/AllDB/AllDB.html', dbs=dbs)


@AllDBs.route('/AddDB', methods=['GET', 'POST'])
@login_required
def AddDB():
    # 从网页取值
    if request.method == 'POST':
        name = request.form.get('name')
        ip = request.form.get('ip')
        port = request.form.get('port')
        note = request.form.get('note')
        deptname = request.form.get('deptId')
        username = request.form.get('username')
        dbs = Dbs(name=name, ip=ip, port=port, note=note)
        db1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
        if db1:
            error = 'already exist.'

        else:
            try:
                db.session.add(dbs)
                db.session.commit()
                error = 'Add DB successfully.'
            except db.IntegrityError:
                error = 'adding error!!!'

        flash(error)

        # 如果分配了部门
        if deptname:
            deptId1 = Departments.query.filter(Departments.deptname == deptname).first()
            if deptId1:
                deptId = deptId1.id
                dbid1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
                dbid = dbid1.id
                db_dept = DbsDept(deptid=deptId, dbid=dbid)
                try:
                    db.session.add(db_dept)
                    db.session.commit()
                except:
                    error = 'adding error!!!'

        # 如果分配了数据库管理者
        if username:
            user1 = User.query.filter(User.name == username).first()
            if user1:
                userId = user1.id
                dbid1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
                dbid = dbid1.id
                db_user = DbsUser(uid=userId, dbid=dbid)
                try:
                    db.session.add(db_user)
                    db.session.commit()
                except:
                    error = 'adding error!!!'

    department = Departments.query.all()
    users = User.query.all()

    return render_template('DBs/AllDB/AddDB.html', department=department, users=users)


## 编辑数据库信息 ##
@AllDBs.route('/UserEdit/<dbname>/', methods=['GET', 'POST'])
@login_required
def EditDB(dbname):
    # 获取用户信息
    dbs = Dbs.query.filter_by(name=dbname).first()
    # 确认更改
    if request.method == 'POST':
        name = request.form.get('name')
        ip = request.form.get('ip')
        port = request.form.get('port')
        note = request.form.get('note')
        deptname = request.form.get('deptId')
        username = request.form.get('username')

        # 修改部门信息
        if deptname:
            deptId1 = Departments.query.filter(Departments.deptname == deptname).first()
            if deptId1:
                deptId = deptId1.id
                dbid1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
                dbid = dbid1.id
                db_dept = DbsDept(deptid=deptId, dbid=dbid)
                try:
                    db.session.add(db_dept)
                    db.session.commit()
                except:
                    error = 'adding error!!!'

        # 修改数据库管理者
        if username:
            user1 = User.query.filter(User.name == username).first()
            if user1:
                userId = user1.id
                dbid1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
                dbid = dbid1.id
                db_user = DbsUser(uid=userId, dbid=dbid)
                try:
                    db.session.add(db_user)
                    db.session.commit()
                except:
                    error = 'adding error!!!'

        dbs.name = name
        dbs.ip = ip
        dbs.port = port
        dbs.note = note

        # 提交信息
        db.session.add(dbs)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            flash(e)
            return redirect(url_for('AllDB.AllDB'))

    department = Departments.query.all()
    users = User.query.all()

    return render_template('DBs/AllDB/EditDB.html', dbs=dbs, department=department, users=users)


@AllDBs.route('/delete/<dbname>/', methods=['GET', 'POST'])
@login_required
def delete(dbname):
    dbs = Dbs.query.filter_by(name=dbname).first()
    dbdept = DbsDept.query.filter_by(dbid=dbs.id).first()
    dbuser = DbsUser.query.filter_by(dbid=dbs.id).first()
    if dbdept:
        db.session.delete(dbdept)
    if dbuser:
        db.session.delete(dbuser)
    db.session.delete(dbs)
    db.session.commit()

    return redirect(url_for('AllDB.AllDB'))

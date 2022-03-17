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
    dbs_info = []
    dbs = Dbs.query.all()
    for db_tmp in dbs:
        # 数据库管理员
        db_user = None
        dbuser = DbsUser.query.filter_by(dbid=db_tmp.id).first()
        if dbuser:
            db_user = User.query.filter_by(id=dbuser.uid).first()

        # 数据库所属部门
        dbdepts = DbsDept.query.filter_by(dbid=db_tmp.id).all()
        db_depts = []
        for dbdept in dbdepts:
            db_dept = Departments.query.filter_by(id=dbdept.deptid).first()
            db_dept_tmp = {
                'name': db_dept.deptname
            }
            db_depts.append(db_dept_tmp)

        db_info = {
            'id': db_tmp.id,
            'name': db_tmp.name,
            'ip': db_tmp.ip,
            'port': db_tmp.port,
            'note': db_tmp.note,
            'dbdepts': db_depts,
            'dbuser': db_user
        }
        dbs_info.append(db_info)

    return render_template('DBs/AllDB/AllDB.html', dbs_info=dbs_info)


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
            except Exception as e:
                db.session.rollback()
                db.session.flush()
                error = str(e)
                flash(error)

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
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    error = str(e)
                    flash(error)

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
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    error = str(e)
                    flash(error)

    department = Departments.query.all()
    users = User.query.all()

    return render_template('DBs/AllDB/AddDB.html', department=department, users=users)


## 编辑数据库信息 ##
@AllDBs.route('/UserEdit/<dbname>/', methods=['GET', 'POST'])
@login_required
def EditDB(dbname):
    # 选项中需要的值
    department = Departments.query.all()
    users = User.query.all()
    # 获取数据库信息
    dbs = Dbs.query.filter_by(name=dbname).first()
    # 对此库拥有权限的部门全部列出来
    dbsdept = DbsDept.query.filter_by(dbid=dbs.id).all()
    dbdeptlist = []
    for dbdept in dbsdept:
        dept = Departments.query.filter_by(id=dbdept.deptid).first()
        dbdeptlist.append(dept)

    # 库的管理人员只有一个
    dbuser = None
    dbsuser = DbsUser.query.filter_by(dbid=dbs.id).first()
    if dbsuser:
        dbuser = User.query.filter_by(id=dbsuser.uid).first()

    # 确认更改
    if request.method == 'POST':
        name = request.form.get('name')
        ip = request.form.get('ip')
        port = request.form.get('port')
        note = request.form.get('note')
        deptId = request.form.getlist('deptId')
        username = request.form.get('username')

        # 修改部门信息
        if len(deptId) > 0:
            # 先清空之前的关系
            for dept in dbdeptlist:
                dept_delete = DbsDept.query.filter_by(deptid=dept.id, dbid=dbs.id).first()
                db.session.delete(dept_delete)

            # 再重新添加
            for deptid in deptId:
                deptId1 = Departments.query.filter(Departments.id == deptid).first()
                if deptId1:
                    deptId = deptId1.id
                    dbid1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
                    dbid = dbid1.id
                    db_dept = DbsDept(deptid=deptId, dbid=dbid)
                    try:
                        db.session.add(db_dept)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        db.session.flush()
                        error = str(e)
                        flash(error)
        else:
            # 清空之前的关系
            for dept in dbdeptlist:
                dept_delete = DbsDept.query.filter_by(deptid=dept.id, dbid=dbs.id).first()
                db.session.delete(dept_delete)

        # 修改数据库管理者
        if username:
            user1 = User.query.filter(User.name == username).first()
            dbid1 = Dbs.query.filter(Dbs.name == name and Dbs.ip == ip).first()
            dbid = dbid1.id
            # 查看该数据库有没有管理员
            dbuser = DbsUser.query.filter(DbsUser.dbid == dbid).first()
            if dbuser:
                # 如果有，就清除掉
                db.session.delete(dbuser)

            if user1:
                db_user = DbsUser(uid=user1.id, dbid=dbid)
                try:
                    db.session.add(db_user)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    db.session.flush()
                    error = str(e)
                    flash(error)

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
            flash(str(e))

        return redirect(url_for('AllDB.AllDB'))

    return render_template('DBs/AllDB/EditDB.html', dbs=dbs, department=department, users=users,
                           dbuser=dbuser, dbdeptlist=dbdeptlist)


@AllDBs.route('/delete/<dbname>/', methods=['GET', 'POST'])
@login_required
def delete(dbname):
    dbs = Dbs.query.filter_by(name=dbname).first()
    dbdepts = DbsDept.query.filter_by(dbid=dbs.id).all()
    dbuser = DbsUser.query.filter_by(dbid=dbs.id).first()
    if dbdepts:
        for dbdept in dbdepts:
            db.session.delete(dbdept)
    if dbuser:
        db.session.delete(dbuser)
    db.session.delete(dbs)
    db.session.commit()

    return redirect(url_for('AllDB.AllDB'))

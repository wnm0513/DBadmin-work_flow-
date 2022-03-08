from flask import (
    g, render_template, flash, request, redirect, url_for
)
from flask import (
    g, render_template
)
from sqlalchemy import and_

from app import login_required
from useddb.models import db, User, Departments
from . import Departments_view


@Departments_view.route('/Department')
@login_required
def Dept():
    deptusers = []
    if g.user.is_super():
        depts = Departments.query.all()
    elif g.user.is_manager():
        depts = db.session.query(Departments).filter(Departments.id == g.user.deptId)
    else:
        depts = []
    for dept in depts:
        manager = db.session.query(User.id, User.account, User.name).join(Departments,
                                                                          User.id == Departments.managerid).filter(
            and_(User.deptId == dept.id, User.ismanager == 1)).first()
        ducount = User.query.filter_by(deptId=dept.id).count()
        users = User.query.filter_by(deptId=dept.id).all()
        # 存储各个部门人员的信息
        usersinfo = []
        for user in users:
            userinfo = {
                "account": user.account,
                "name": user.name,
                "role_name": user.role_name,
                "email": user.email,
                "phone": user.phone,
                "ctime": user.ctime,
                "last_login": user.last_login,
            }
            usersinfo.append(userinfo)
        if manager is None:
            mid = 0
            mgrname = "暂无数据"
        else:
            mid = manager.id
            mgrname = manager.name
        deptmanager = {
            "id": dept.id,
            "name": dept.deptname,
            "mid": mid,
            "mgrname": mgrname,
            "deptusercount": ducount,
            "usersinfo": usersinfo
        }
        # 汇总一个部门的所有信息
        deptusers.append(deptmanager)

    return render_template('Usermanage/Department/Departments.html', deptuser=deptusers)


@Departments_view.route('/AddDepartment', methods=['GET', 'POST'])
@login_required
def AddDept():
    # 从网页取值
    if request.method == 'POST':
        deptname = request.form.get('deptname')
        username = request.form.get('username')

        user = User.query.filter_by(name=username).first()
        dept = Departments(deptname=deptname, managerid=user.id)
        dept1 = Departments.query.filter(Departments.deptname == deptname).first()
        if dept1:
            error = 'already exist.'

        else:
            try:
                db.session.add(dept)
                db.session.commit()
                error = 'Add Department successfully.'
            except Exception as e:
                error = str(e)

        if user.ismanager == 0:
            user.ismanager = 1
        else:
            user.ismanager = 1

        flash(error)
        return redirect(url_for('Department.Dept'))

    department = Departments.query.all()
    users = User.query.all()

    return render_template('Usermanage/Department/AddDept.html', department=department, users=users)


## 移除部门 ##
@Departments_view.route('/delete/<id>/', methods=['GET', 'POST'])
@login_required
def delete(id):
    user = Departments.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('Department.Dept'))

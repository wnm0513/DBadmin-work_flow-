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
                "status": user.status
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
    department = Departments.query.all()
    users = User.query.all()
    # 从网页取值
    if request.method == 'POST':
        deptname = request.form.get('deptname')
        username = request.form.get('username')

        user = User.query.filter_by(name=username).first()
        dept1 = Departments.query.filter(Departments.deptname == deptname).first()
        if dept1:
            error = '部门已存在！'
            flash(error)
            return render_template('Usermanage/Department/AddDept.html', department=department, users=users)

        else:
            dept = Departments(deptname=deptname, managerid=user.id)
            db.session.add(dept)
            db.session.commit()

            # 选择部门经理时做的判断，如果不是就先更改再关联部门
            if user.ismanager == 0:
                dept2 = Departments.query.filter(Departments.deptname == deptname).first()
                user.ismanager = 1
                user.deptId = dept2.id
            # 如果是就直接关联部门
            else:
                dept2 = Departments.query.filter(Departments.deptname == deptname).first()
                user.deptId = dept2.id
            try:
                db.session.add(user)
                db.session.commit()
                error = 'Add Department successfully.'
            except Exception as e:
                error = str(e)

        flash(error)
        return redirect(url_for('Department.Dept'))

    return render_template('Usermanage/Department/AddDept.html', department=department, users=users)


## 移除部门 ##
@Departments_view.route('/delete/<id>/', methods=['GET', 'POST'])
@login_required
def delete(id):
    # 删除部门
    dept = Departments.query.filter_by(id=id).first()
    db.session.delete(dept)
    db.session.commit()

    # 修改用户的部门Id
    users = User.query.filter_by(deptId=id).all()
    for user in users:

        if user.ismanager == 1:
            user.ismanager = 0

        user.deptId = 0
        db.session.add(user)
        db.session.commit()

    return redirect(url_for('Department.Dept'))

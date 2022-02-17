from flask import (
    g, render_template
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
def dept():
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

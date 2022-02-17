from flask import (
    g, render_template
)
from sqlalchemy import and_

from app import login_required
from useddb.models import db, User, Departments, DbsDept, Dbs
from . import DeptDBs


@DeptDBs.route('/DeptDB', methods=['GET', 'POST'])
@login_required
def DeptDB():
    deptdbs = []
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
        ducount = DbsDept.query.filter_by(deptid=dept.id).count()
        dbids = DbsDept.query.filter_by(deptid=dept.id).all()
        for dbid in dbids:
            dbs = Dbs.query.filter_by(id=dbid.dbid).all()
            # 存储各个部门数据库的信息
            dbsinfo = []
            for dbs1 in dbs:
                dbinfo = {
                    "name": dbs1.name,
                    "ip": dbs1.ip,
                    "port": dbs1.port,
                    "note": dbs1.note,
                }
                dbsinfo.append(dbinfo)
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
                    "deptdbcount": ducount,
                    "dbsinfo": dbsinfo
                }
                # 汇总一个部门的所有信息
                deptdbs.append(deptmanager)

    return render_template('DBs/DeptDB/DeptDB.html', deptdbs=deptdbs)

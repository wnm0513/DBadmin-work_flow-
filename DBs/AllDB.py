from flask import (
    g, render_template, request, flash
)
from sqlalchemy import and_, func

from app import login_required
from useddb.models import db, User, Departments, Dbs, DbsDept
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
        func.group_concat(Departments.deptname)
    ).outerjoin(DbsDept, DbsDept.dbid == Dbs.id) \
        .outerjoin(Departments, Departments.id == DbsDept.deptid).group_by(Dbs.id).order_by(Dbs.name.desc())

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

    department = Departments.query.all()

    return render_template('DBs/AllDB/AddDB.html', department=department)

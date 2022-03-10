from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy import and_

from app import login_required
from useddb.models import Workorder, db, Departments, WorkFlow
from . import OrderHistories


@OrderHistories.route('/OrderHistories')
@login_required
def OrderHistory():
    # 定义列表
    workordersinfo = []

    # 查询工单，并以权限分类用户能看到的正在进行的工单
    if g.user.is_super():
        workorders = Workorder.query.filter(Workorder.status == 0).all()
    elif g.user.is_manager():
        workorders = db.session.query(Workorder).filter(
            and_(Workorder.deptid == g.user.deptId, Workorder.status == 0)).all()
    else:
        workorders = db.session.query(Workorder).filter(and_(Workorder.uid == g.user.id, Workorder.status == 0)).all()

    for workorder in workorders:
        deptname = db.session.query(Departments.deptname).filter(Departments.id == workorder.deptid)
        workflow = WorkFlow.query.filter(WorkFlow.woid == workorder.id).first()
        workorderinfo = {
            'id': workorder.id,
            'uname': workflow.uname,
            'deptname': deptname,
            'stime': workorder.stime,
            'type': workorder.applyreason,
            'nowstep': workflow.nowstep,
            'auditing': workflow.auditing,
            'status': workorder.status
        }
        workordersinfo.append(workorderinfo)

    return render_template('workorder/OrderHistory/OrderHistory.html')
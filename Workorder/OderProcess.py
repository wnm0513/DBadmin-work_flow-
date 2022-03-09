from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app import login_required
from useddb.models import WorkFlow, Workorder, db, Departments
from . import OrderProcesses


@OrderProcesses.route('/OrderProcess')
@login_required
def OrderProcess():
    # 定义列表
    workordersinfo = []

    # 查询工单，并以权限分类用户能看到的工单
    if g.user.is_super():
        workorders = Workorder.query.all()
    elif g.user.is_manager():
        workorders = db.session.query(Workorder).filter(Workorder.deptid == g.user.deptId).all()
    else:
        workorders = db.session.query(Workorder).filter(Workorder.uid == g.user.id).all()

    for workorder in workorders:
        deptname = db.session.query(Departments.deptname).filter(Departments.id == workorder.deptid)
        workflow = WorkFlow.query.filter(WorkFlow.woid == workorder.id).first()
        workorderinfo = {
            'uname': workflow.uname,
            'deptname': deptname,
            'stime': workorder.stime,
            'type': workorder.applyreason,
            'nowstep': workflow.nowstep,
            'status': workorder.status
        }
        workordersinfo.append(workorderinfo)

    return render_template('workorder/OrderProcess/OrderProcess.html', workordersinfo=workordersinfo)

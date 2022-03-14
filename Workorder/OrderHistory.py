import datetime

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy import and_

from app import login_required
from useddb.models import Workorder, db, Departments, WorkFlow, InceptionRecordsExecute, InceptionRecords
from . import OrderHistories
from .MineWorkorder import path


@OrderHistories.route('/OrderHistories')
@login_required
def OrderHistory():
    # 定义列表
    workordersinfo = []

    # 查询工单，并以权限分类用户能看到的正在进行的工单
    if g.user.is_super():
        workorders = Workorder.query.all()
    elif g.user.is_manager():
        workorders = db.session.query(Workorder).filter(Workorder.deptid == g.user.deptId).all()
    else:
        workorders = db.session.query(Workorder).filter(Workorder.uid == g.user.id).all()

    for workorder in workorders:
        dept = db.session.query(Departments).filter(Departments.id == workorder.deptid).first()
        workflow = WorkFlow.query.filter(WorkFlow.woid == workorder.id).first()
        # 取出sqlcheck信息， 准备给被驳回和取消的工单
        sqls_info = InceptionRecords.query.filter(InceptionRecords.filename == workorder.filename).all()

        # 从记录执行过的sql的表中取出数据整合
        sqlsinfo = []
        for sqlinfo in sqls_info:
            sqlinfos = {
                'sqltext': sqlinfo.sqltext
            }
            sqlsinfo.append(sqlinfos)

        # 取出执行过的信息给已通过和回滚的工单
        executedsqls = InceptionRecordsExecute.query.filter(InceptionRecordsExecute.woid == workorder.id).all()

        # 从记录执行过的sql的表中取出数据整合
        executedsqlsinfo = []
        for executedsql in executedsqls:
            executedsqlinfo = {
                'exetime': executedsql.exetime,
                'sqltext': executedsql.sqltext,
                'affrows': executedsql.affrows,
                'executetime': executedsql.executetime,
                'exstatus': executedsql.exstatus
            }
            executedsqlsinfo.append(executedsqlinfo)

        workorderinfo = {
            'id': workorder.id,
            'uname': workflow.uname,
            'deptname': dept.deptname,
            'stime': workorder.stime,
            'type': workorder.applyreason,
            'nowstep': workflow.nowstep,
            'auditing': workflow.auditing,
            'status': workorder.status,
            'executedsqlsinfo': executedsqlsinfo,
            'sqlsinfo': sqlsinfo
        }
        workordersinfo.append(workorderinfo)

    return render_template('workorder/OrderHistory/OrderHistory.html', workordersinfo=workordersinfo)

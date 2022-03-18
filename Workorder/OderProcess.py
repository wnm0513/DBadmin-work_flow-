import datetime

import pymysql
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from sqlalchemy import and_

from app import login_required
from config import Config
from useddb.models import WorkFlow, Workorder, db, Departments, InceptionRecordsExecute
from . import OrderProcesses
from .MineWorkorder import goinceptionCheck, goinceptionExecute

path = Config.INCEPTION_PATH


@OrderProcesses.route('/OrderProcess')
@login_required
def OrderProcess():
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

    g.order_count = len(workorders)
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

    return render_template('workorder/OrderProcess/OrderProcess.html', workordersinfo=workordersinfo)


@OrderProcesses.route('/OrderDetail/<id>')
@login_required
def OrderDetail(id):
    # 引用全局变量
    global path
    # 定义列表
    sqlsinfo = []

    # 查询对应的工单
    workorder = db.session.query(Workorder).filter_by(id=id).first()
    workflow = db.session.query(WorkFlow).filter_by(woid=id).first()
    date = datetime.datetime.strptime(str(workorder.stime), '%Y-%m-%d %H:%M:%S').date()
    orderdate = str(date).replace('-', '')

    # 读取文件
    filecontent = open('{path}/{day}/{filename}'.format(path=path, day=orderdate, filename=workorder.filename),
                       'r')
    allsqls = filecontent.readlines()
    # 将最后一行的dbname取出来
    dbnamelist = allsqls.pop().split()
    filecontent.close()

    for allsql in allsqls:

        sqlresults = goinceptionCheck(allsql)

        for sqlresult in sqlresults:
            # 整合check结果
            sqlinfo = {
                'stage': sqlresult[1],
                'error_level': sqlresult[2],
                'stage_status': sqlresult[3],
                'error_message': sqlresult[4],
                'sql': sqlresult[5],
                'affected_rows': sqlresult[6],
                'execute_time': sqlresult[9],
                'backup_time': sqlresult[11]
            }
            sqlsinfo.append(sqlinfo)

    # 当别的视图请求时
    if request.method == 'GET':
        return render_template('workorder/OrderProcess/OrderDetail.html', sqlsinfo=sqlsinfo, workorder=workorder,
                               workflow=workflow)


## 同意 ##
@OrderProcesses.route('/agree/<woid>/', methods=['GET', 'POST'])
@login_required
def agree(woid):
    workflow = WorkFlow.query.filter(WorkFlow.woid == woid).first()

    # 经理审核
    if workflow.nowstep == 1:
        workflow.nowstep = 2

    # DBA审核
    elif workflow.nowstep == 2:
        workflow.nowstep = 3
        if workflow.nowstep == workflow.maxstep:
            workflow.auditing = 1

    # 提交
    try:
        db.session.add(workflow)
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

    return redirect(url_for('OrderProcess.OrderProcess'))


## 执行 ##
@OrderProcesses.route('/execute/<woid>/', methods=['GET', 'POST'])
@login_required
def execute(woid):
    workorder = Workorder.query.filter(Workorder.id == woid).first()
    date = datetime.datetime.strptime(str(workorder.stime), '%Y-%m-%d %H:%M:%S').date()
    orderdate = str(date).replace('-', '')

    # 读取文件
    filecontent = open('{path}/{day}/{filename}'.format(path=path, day=orderdate, filename=workorder.filename),
                       'r')
    allsqls = filecontent.readlines()
    # 将最后一行的dbname取出来
    dbnamelist = allsqls.pop().split()
    filecontent.close()

    for allsql in allsqls:

        # 执行
        sqlresults = goinceptionExecute(allsql)

        for sqlresult in sqlresults:
            # 记录执行结果
            executedsql = InceptionRecordsExecute(woid=woid, sequence=sqlresult[7], exetime=datetime.datetime.now(),
                                                  sqltext=sqlresult[5], affrows=sqlresult[6], executetime=sqlresult[9],
                                                  exstatus=sqlresult[3], extype=1, opid_time=sqlresult[7],
                                                  backup_dbname=sqlresult[8])

            # 提交
            try:
                db.session.add(executedsql)
                db.session.commit()
            except Exception as e:
                error = str(e)
                flash(error)

    # 表示工单已通过
    workorder.status = 1
    workorder.etime = datetime.datetime.now()

    # 提交
    try:
        db.session.add(workorder)
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

    return redirect(url_for('OrderProcess.OrderProcess'))


## 驳回 ##
@OrderProcesses.route('/refused/<woid>/', methods=['GET', 'POST'])
@login_required
def refused(woid):
    workorder = Workorder.query.filter(Workorder.id == woid).first()

    workflow = WorkFlow.query.filter(WorkFlow.woid == woid).first()

    # 表示工单未通过
    workorder.status = 2

    # 表示在审批流中被拒绝
    workflow.auditing = 2

    # 提交
    try:
        db.session.add(workorder, workflow)
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

    return redirect(url_for('OrderProcess.OrderProcess'))


## 取消 ##
@OrderProcesses.route('/canncel/<woid>/', methods=['GET', 'POST'])
@login_required
def cancel(woid):
    try:
        db.session.query(Workorder).filter(Workorder.id == woid).delete()
        db.session.query(WorkFlow).filter(WorkFlow.woid == woid).delete()
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

    return redirect(url_for('OrderProcess.OrderProcess'))

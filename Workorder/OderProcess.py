import datetime

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app import login_required
from config import Config
from useddb.models import WorkFlow, Workorder, db, Departments
from . import OrderProcesses
from .MineWorkorder import goinceptionCheck

path = Config.INCEPTION_PATH


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
            'id': workorder.id,
            'uname': workflow.uname,
            'deptname': deptname,
            'stime': workorder.stime,
            'type': workorder.applyreason,
            'nowstep': workflow.nowstep,
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
        return render_template('workorder/OrderProcess/OrderDetail.html', sqlsinfo=sqlsinfo, workorder=workorder, workflow=workflow)







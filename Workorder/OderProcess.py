import datetime

import pymysql
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from sqlalchemy import and_

from login_required import login_required
from config import Config
from useddb.models import Workorder, db, Departments, InceptionRecordsExecute, User
from . import OrderProcesses, send_mail, send_dingding
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
        workorderinfo = {
            'id': workorder.id,
            'uname': workorder.username,
            'deptname': deptname,
            'stime': workorder.stime,
            'type': workorder.applyreason,
            'process_status': workorder.process_status,
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
    date = datetime.datetime.strptime(str(workorder.stime), '%Y-%m-%d %H:%M:%S').date()
    orderdate = str(date).replace('-', '')

    # 读取文件
    filecontent = open('{path}/{day}/{filename}'.format(path=path, day=orderdate, filename=workorder.filename),
                       'r')
    allsqls = filecontent.readlines()
    # 将最后一行的dbname取出来
    dbnamelist = allsqls.pop().split()
    filecontent.close()

    for num in range(len(dbnamelist)):

        # 调用goinceptioncheck获取check结果
        sqlresults = goinceptionCheck(dbnamelist[num], allsqls[num])

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
        return render_template('workorder/OrderProcess/OrderDetail.html', sqlsinfo=sqlsinfo, workorder=workorder)


## 同意 ##
@OrderProcesses.route('/agree/<woid>/', methods=['GET', 'POST'])
@login_required
def agree(woid):
    workorder = Workorder.query.filter(Workorder.id == woid).first()

    # 经理审核
    if workorder.process_status == 1:
        workorder.process_status = 2
        workorder.process_otime = datetime.datetime.now()

        # 消息推送DBA
        send_dept = Departments.query.filter_by(id=workorder.deptid).first()
        receive_DBA = User.query.filter_by(id=4).first()
        send_user = User.query.filter_by(name=workorder.username).first()
        content = "您好，{confirm_user}，有新的工单待您审批：\n" \
                  "审批单号：{woid}，\n" \
                  "发起人：{user}，\n" \
                  "发起部门：{dept}，\n" \
                  "申请理由：{reason}\n\n" \
                  "请登录DBAdmin查看待审批内容！\n地址：http://{ip}" \
            .format(woid=workorder.id,
                    user=send_user.name,
                    dept=send_dept.deptname,
                    reason=workorder.applyreason,
                    confirm_user=receive_DBA.name,
                    ip=Config.WEB_IP
                    )
        # send_mail(content, receive_DBA.email)
        # send_dingding(content, receive_DBA.ding)

    # DBA审核
    elif workorder.process_status == 2:
        workorder.process_status = 3
        workorder.process_otime = datetime.datetime.now()

        # 消息推送
        send_dept = Departments.query.filter_by(id=workorder.deptid).first()
        send_user = User.query.filter_by(name=workorder.username).first()
        content = "您好，{confirm_user}，您的工单已通过审批，请执行：\n" \
                  "审批单号：{woid}，\n" \
                  "发起人：{user}，\n" \
                  "发起部门：{dept}，\n" \
                  "申请理由：{reason}\n\n" \
                  "请登录DBAdmin查看待审批内容！\n地址：http://{ip}" \
            .format(woid=workorder.id,
                    user=send_user.name,
                    dept=send_dept.deptname,
                    reason=workorder.applyreason,
                    confirm_user=send_user.name,
                    ip=Config.WEB_IP
                    )
        # send_mail(content, send_user.email)
        # send_dingding(content, send_user.ding)

    # 提交
    try:
        db.session.add(workorder)
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

    for num in range(len(dbnamelist)):

        # 执行
        sqlresults = goinceptionExecute(dbnamelist[num], allsqls[num])

        for sqlresult in sqlresults:
            # 记录执行结果
            executedsql = InceptionRecordsExecute(woid=woid, sequence=sqlresult[7], exetime=datetime.datetime.now(),
                                                  sqltext=sqlresult[5], errorinfo=sqlresult[4], affrows=sqlresult[6], executetime=sqlresult[9],
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

    # 表示工单未通过
    workorder.status = 2

    # 表示在审批流中被拒绝
    if workorder.process_status == 1:
        workorder.process_status = 4  # 表示经理驳回
        workorder.process_otime = datetime.datetime.now()

    if workorder.process_status == 2:
        workorder.process_status = 5  # 表示DBA驳回
        workorder.process_otime = datetime.datetime.now()

    # 提交
    try:
        db.session.add(workorder)
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

        # 消息推送
        send_dept = Departments.query.filter_by(id=workorder.deptid).first()
        send_user = User.query.filter_by(name=workorder.username).first()
        content = "您好，{confirm_user}，您的工单已被驳回：\n" \
                  "审批单号：{woid}，\n" \
                  "发起人：{user}，\n" \
                  "发起部门：{dept}，\n" \
                  "申请理由：{reason}\n\n" \
                  "请登录DBAdmin查看！\n地址：http://{ip}" \
            .format(woid=workorder.id,
                    user=send_user.name,
                    dept=send_dept.deptname,
                    reason=workorder.applyreason,
                    confirm_user=send_user.name,
                    ip=Config.WEB_IP
                    )
        # send_mail(content, send_user.email)
        # send_dingding(content, send_user.ding)

    return redirect(url_for('OrderProcess.OrderProcess'))


## 取消 ##
@OrderProcesses.route('/canncel/<woid>/', methods=['GET', 'POST'])
@login_required
def cancel(woid):
    try:
        db.session.query(Workorder).filter(Workorder.id == woid).delete()
        db.session.commit()
    except Exception as e:
        error = str(e)
        flash(error)

    return redirect(url_for('OrderProcess.OrderProcess'))

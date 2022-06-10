import datetime

import pymysql
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy import and_, between, text

from login_required import login_required
from config import Config
from useddb import models
from useddb.models import Workorder, db, Departments, WorkFlow, InceptionRecordsExecute, InceptionRecords, RollBack
from . import OrderHistories
from .MineWorkorder import path


@OrderHistories.route('/OrderHistories', methods=['GET', 'POST'])
@login_required
def OrderHistory():
    # 定义列表
    workordersinfo = []

    # 查询工单，并以权限分类用户能看到完成的工单
    if g.user.is_super():
        workorders = Workorder.query.order_by(text('-etime')).all()
    elif g.user.is_manager():
        workorders = db.session.query(Workorder).filter(Workorder.deptid == g.user.deptId)\
            .order_by(text('-etime')).all()
    else:
        workorders = db.session.query(Workorder).filter(Workorder.uid == g.user.id)\
            .order_by(text('-etime')).all()

    # 如果选择了时间区间
    if request.method == 'POST':
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        if g.user.is_super():
            workorders = db.session.query(Workorder)\
                .filter(Workorder.etime.between(start_time, end_time)).order_by(text('-etime')).all()
        elif g.user.is_manager():
            workorders = db.session.query(Workorder)\
                .filter(and_(Workorder.deptid == g.user.deptId, Workorder.etime.between(start_time, end_time)))\
                .order_by(text('-etime')).all()
        else:
            workorders = db.session.query(Workorder)\
                .filter(and_(Workorder.uid == g.user.id, Workorder.etime.between(start_time, end_time)))\
                .order_by(text('-etime')).all()

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
                'opid_time': executedsql.sequence,
                'exstatus': executedsql.exstatus
            }
            executedsqlsinfo.append(executedsqlinfo)

        workorderinfo = {
            'id': workorder.id,
            'uname': workflow.uname,
            'deptname': dept.deptname,
            'etime': workorder.etime,
            'type': workorder.applyreason,
            'nowstep': workflow.nowstep,
            'auditing': workflow.auditing,
            'status': workorder.status,
            'executedsqlsinfo': executedsqlsinfo,
            'sqlsinfo': sqlsinfo
        }
        workordersinfo.append(workorderinfo)

    return render_template('workorder/OrderHistory/OrderHistory.html', workordersinfo=workordersinfo)


@OrderHistories.route('/rollback/<woid>')
@login_required
def rollback(woid):
    # 此段分别用两个账号操作数据库，一个在备份实例，一个在目标实例
    # 这里查询inception执行过的SQL记录表
    inception_executeds = db.session.query(InceptionRecordsExecute).filter(InceptionRecordsExecute.woid == woid).all()
    # 取出opid_time的值
    conn_backup_db = pymysql.connect(
        host=Config.INCEPTION_BACKUP_HOST,
        port=int(Config.INCEPTION_BACKUP_PORT),
        user=Config.INCEPTION_BACKUP_USER,
        password=Config.INCEPTION_BACKUP_PASSWORD)

    # 初始化备份数据库的游标
    cur = conn_backup_db.cursor()
    # 将回滚信息写入回滚表
    for inception_executed in inception_executeds:
        rollback_opidtime = inception_executed.sequence
        rollback_dbname = inception_executed.backup_dbname

        # 数据库交互查询回滚语句
        s_host = "select host from "
        s_table = "select tablename from "
        s_sql = "select rollback_statement from "
        table = ".$_$Inception_backup_information$_$ "
        condition = " where  opid_time='{opid_time}';".format(opid_time=rollback_opidtime)
        rollbackhost = s_host + rollback_dbname + table + condition
        cur.execute(rollbackhost)
        host = cur.fetchall()
        rollback_host = host[0][0]

        rollbacktbname = s_table + rollback_dbname + table + condition
        cur.execute(rollbacktbname)
        tbname = cur.fetchall()
        rollback_tbname = tbname[0][0]

        if rollback_tbname:
            rollbackstatement = s_sql + rollback_dbname + '.' + rollback_tbname + condition
            cur.execute(rollbackstatement)
            rollback_sql = cur.fetchall()
        else:
            rollback_sql = "查询回滚语句出错，请联系DBA处理！;"

        rollback_info = RollBack(woid=woid, opid_time=rollback_opidtime, sqltext=rollback_sql,
                                 tablename=rollback_tbname, dbname=rollback_dbname, host=rollback_host,
                                 create_time=datetime.datetime.now())
        db.session.add(rollback_info)
        db.session.commit()

    cur.close()
    conn_backup_db.close()

    rollback_all = RollBack.query.filter_by(woid=woid).all()
    for rollback_one in rollback_all:
        rollbacksql = rollback_one.sqltext

        # 执行回滚语句
        conn_rollback = pymysql.connect(
            host=rollback_one.host,
            port=int(Config.PORT),
            user=Config.MYSQLUSER,
            password=Config.MYSQLPASSWORD
        )
        # 初始化游标
        cur_execute = conn_rollback.cursor()
        # 执行
        cur_execute.execute(rollbacksql)

        cur.close()
        conn_rollback.close()

    workorder = Workorder.query.filter_by(id=woid).first()
    # 将工单状态调整为已回滚
    workorder.status = 3
    
    db.session.add(workorder)
    db.session.commit()

    return redirect(url_for('OrderHistory.OrderHistory'))

import datetime
import re

from flask import Flask, render_template_string, jsonify
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib

from sqlalchemy import distinct
from sqlalchemy.sql.functions import count

import useddb
import pymysql
import redis
import rediscluster
from login_required import login_required
from config import Config
from useddb import models
from useddb.models import db, User, UsersRoles, Departments, Dbs, DbsDept, DbsUser, QueryHistory, Instance, \
    InstanceQueryHistory
from . import RedisExecutes

redisCluster = [{'host': '192.168.200.176', 'port': 7000},
                {'host': '192.168.200.176', 'port': 7001},
                {'host': '192.168.200.176', 'port': 7002},
                {'host': '192.168.200.176', 'port': 7003},
                {'host': '192.168.200.176', 'port': 7004},
                {'host': '192.168.200.176', 'port': 7005}]


def Redis_conn_exec(select_env, select_db, sql):
    instance = Instance.query.filter_by(instance_name=select_env).first()

    # if instance.status == 2:
    #     if instance.password == 'null':
    #         r = rediscluster.RedisCluster(startup_nodes=redisCluster)
    #     else:
    #         r = rediscluster.RedisCluster(startup_nodes=redisCluster, password=instance.password)
    # else:
    if instance.password == 'null':
        r = redis.StrictRedis(host=instance.host, db=select_db, port=instance.port, decode_responses=True)
    else:
        r = redis.StrictRedis(host=instance.host, db=select_db, port=instance.port,
                              password=instance.password, decode_responses=True)

    result = r.execute_command(sql)

    r.close()

    return result


def query_check(sql=''):
    """提交查询前的检查"""
    result = {'msg': '', 'bad_query': True, 'filtered_sql': sql, 'has_star': False}
    safe_cmd = ["exists", "ttl", "pttl", "type", "get", "mget", "strlen",
                "hgetall", "hexists", "hget", "hmget", "hkeys", "hvals",
                "smembers", "scard", "sdiff", "sunion", "sismember", "llen", "lrange", "lindex"]
    # 命令校验，仅可以执行safe_cmd内的命令
    for cmd in safe_cmd:
        if re.match(cmd, sql.strip(), re.I):
            result['bad_query'] = False
            break
    if result['bad_query']:
        result['msg'] = "禁止执行该命令！"
    return result


@RedisExecutes.route('/changeselectfield/', methods=['GET', 'POST'])
def changeselectfield():
    if request.method == "POST":
        data = request.get_json()
        instance = Instance.query.filter_by(instance_name=data['name']).first()
        if instance.status == 1:
            dbs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        else:
            dbs = ['Redis']
        return jsonify(dbs)
    else:
        return {}


@RedisExecutes.route('/RedisGET', methods=['GET', 'POST'])
@login_required
def RedisGet():
    flag = 0
    select_env = '--请选择实例--'
    select_db = '--请选择数据库--'
    result = []
    sqltext = ''
    instance = Instance.query.all()

    if request.method == 'POST':
        select_env = request.form.get('select_env')
        select_db = request.form.get('select_db')
        sqltext = request.form.get('sqltext')

        if select_env == '--请选择实例--':
            error = "请选择实例！"
            flash(error)

        if select_db == '--请选择数据库--':
            error = "请选择数据库！"
            flash(error)

        sqltext_check = query_check(sql=sqltext)
        if sqltext_check['msg'] == '禁止执行该命令！':
            error = "禁止执行该命令！"
            flash(error)
        else:
            result = Redis_conn_exec(select_env, select_db, sqltext)

        try:
            select_record = InstanceQueryHistory(uid=g.user.id, name=g.user.name, dbname=select_db,
                                                 sqltext=sqltext, select_env=select_env,
                                                 create_time=datetime.datetime.now())
            db.session.add(select_record)
            db.session.commit()

        except Exception as e:
            error = str(e)
            flash(error)

        flag = 1

    return render_template('SQL/Execute/RedisExecute.html', instance=instance, result=result,
                           s_sql=sqltext, s_env=select_env, s_db=select_db, flag=flag)

import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib

from sqlalchemy import text

import useddb
import pymysql
from login_required import login_required
from useddb.models import db, User, UsersRoles, Departments, QueryHistory, Dbs, DbsDept, InstanceQueryHistory
from . import RedisExecutesHistory


@RedisExecutesHistory.route('/RedissqlExecute', methods=['GET', 'POST'])
@login_required
def RedisHistory():
    # 根据用户权限选择可选择查询的数据库
    if g.user.is_super():
        queryhistory = InstanceQueryHistory.query.order_by(text('-create_time')).all()
    else:
        queryhistory = InstanceQueryHistory.query.filter_by(uid=g.user.id).order_by(text('-create_time')).all()

    return render_template('SQL/History/RedisHistory.html', queryhistory=queryhistory)

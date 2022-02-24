import datetime

from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import hashlib
import useddb
import pymysql
from app import login_required
from useddb.models import db, User, UsersRoles, Departments
from . import sqlHistories


## 用户管理 ##
@sqlHistories.route('/sqlExecute', methods=['GET', 'POST'])
@login_required
def sqlHistory():
    return render_template('SQL/History/sqlHistory.html')

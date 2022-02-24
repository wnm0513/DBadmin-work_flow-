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
from . import sqlExecutes


## 用户管理 ##
@sqlExecutes.route('/sqlExecute', methods=['GET', 'POST'])
@login_required
def sqlExecute():
    return render_template('SQL/Execute/sqlExecute.html')

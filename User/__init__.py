from flask import Flask
from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

import useddb
import pymysql
from useddb.models import db, User

# 用户管理
AllUsers = Blueprint('AllUser', __name__)

# 部门管理
Departments_view = Blueprint('Department', __name__)

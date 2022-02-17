from flask import (
    g, render_template
)
from sqlalchemy import and_

from app import login_required
from useddb.models import db, User, Departments
from . import DeptDBs


@DeptDBs.route('/DeptDB', methods=['GET', 'POST'])
@login_required
def DeptDB():
    return render_template('dbs/DeptDB.html')

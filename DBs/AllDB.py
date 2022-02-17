from flask import (
    g, render_template
)
from sqlalchemy import and_

from app import login_required
from useddb.models import db, User, Departments
from . import AllDBs


@AllDBs.route('/AllDB', methods=['GET', 'POST'])
@login_required
def AllDB():
    return render_template('dbs/AllDB.html')

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app import login_required
from . import MineWorkorders


@MineWorkorders.route('/MineWorkorder')
@login_required
def MineWorkorder():
    return render_template('workorder/MineWorkorder/MineWorkorder.html')

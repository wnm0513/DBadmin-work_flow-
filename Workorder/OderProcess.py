from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app import login_required
from . import OrderProcesses


@OrderProcesses.route('/OrderProcess')
@login_required
def OrderProcess():
    return render_template('workorder/OrderProcess/OrderProcess.html')

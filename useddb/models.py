import datetime

from flask import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# 用户表
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account = db.Column(db.String(20), nullable=False, unique=True, )  # comment='账户')
    name = db.Column(db.String(20), nullable=False, default='', )
    passwd = db.Column(db.String(100), nullable=False, )  # comment='密码')
    email = db.Column(db.String(30), nullable=False, default='', )  # comment='邮箱')
    phone = db.Column(db.String(30), nullable=False, default='', )  # comment='手机')
    ding = db.Column(db.String(64), nullable=False, default='', )  # comment='dingding')
    deptId = db.Column(db.Integer, nullable=False, default=0, )  # comment='id')
    answer = db.Column(db.String(64), nullable=False, default='banksteel', )  # comment='密保答案')
    issuper = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='超管0普通，1超管')
    ismanager = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='经理0普通，1经理')
    ctime = db.Column(db.DATETIME, nullable=False, default=datetime.datetime.now(), )  # comment='创建时间')
    utime = db.Column(db.DATETIME, nullable=False, default=datetime.datetime.now(), )  # comment='修改时间')
    last_login = db.Column(db.DATETIME, nullable=False, default=datetime.datetime.now(), )  # comment='最近登录')
    profile = db.Column(db.String(64), nullable=False, default='#', )  # comment='头像')
    role_name = db.Column(db.String(32), nullable=False, unique=True, default='', )  # comment='角色名')
    status = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='状态0异常，1正常')

    def __repr__(self):
        return '<User %r>' % self.account

    @property
    def is_start(self):
        # 判断用户是否启用，如果不启用，什么都不能操作
        user = User.query.filter_by(account=self.account).first()
        if user.status == 1:
            return True
        else:
            return False

    def is_super(self):
        # 判断用户是否为管理员
        user = User.query.filter_by(account=self.account).first()
        if user.issuper == 1:
            return True
        else:
            return False

    def get_id(self):
        # 取id值
        return str(self.id)

    def is_manager(self):
        # 判断用户是否为经理
        user = User.query.filter_by(account=self.account).first()
        if user.ismanager == 1:
            return True
        else:
            return False

    def is_exists(self):
        # 判断账号是否存在
        user = User.query.filter_by(account=self.account).first()
        if user.id:
            return True
        else:
            return False


# 部门表
class Departments(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deptname = db.Column(db.String(64), nullable=False, default='', )  # comment='部门名称')
    managerid = db.Column(db.Integer, nullable=False, default=0, )  # comment='经理id')

    def __repr__(self):
        return '<Departments %r>' % self.id


# 职位
class UsersRoles(db.Model):
    '''工作表'''
    __tablename__ = 'users_roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, )
    role_name = db.Column(db.String(64), nullable=False, default='', index=True)

    def __repr__(self):
        return '<UsersRoles %r>' % self.id


# 数据库表
class Dbs(db.Model):
    '''工作表'''
    __tablename__ = 'dbs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip = db.Column(db.String(20), nullable=False, default='', )  # comment='ip')
    port = db.Column(db.Integer, nullable=False, default=0, )  # comment='端口')
    name = db.Column(db.String(50), nullable=False, default='', )  # comment='数据库名称')
    note = db.Column(db.String(50), nullable=False, default='', )  # comment='备注')

    def __repr__(self):
        return '<Dbs %r>' % self.id


class DbsDept(db.Model):
    '''工作表'''
    __tablename__ = 'dbs_dept'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dbid = db.Column(db.Integer, nullable=False, default=0, )  # comment='DBid')
    deptid = db.Column(db.Integer, nullable=False, default=0, )  # comment='部门id')
    note = db.Column(db.String(50), nullable=False, default='', )  # comment='备注')

    def __repr__(self):
        return '<DbsDept %r>' % self.id


class DbsUser(db.Model):
    '''工作表'''
    __tablename__ = 'dbs_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dbid = db.Column(db.Integer, nullable=False, default=0, )  # comment='DBid')
    uid = db.Column(db.Integer, nullable=False, default=0, )  # comment='用户id')
    note = db.Column(db.String(50), nullable=False, default='', )  # comment='备注')

    def __repr__(self):
        return '<DbsDept %r>' % self.id


# 工单表
class Workorder(db.Model):
    '''工作表'''
    __tablename__ = 'workorder'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False, default=0, )  # comment='用户ID')
    deptid = db.Column(db.Integer, index=True, nullable=False, default=0, )  # comment='部门ID')
    username = db.Column(db.String(20), nullable=False, default='', )  # comment='姓名')
    filename = db.Column(db.String(64), index=True, nullable=False, default=0, )  # comment='SQL文件名')
    stime = db.Column(db.DATETIME, default=datetime.datetime.now(), nullable=False, )  # comment='工单开始时间')
    etime = db.Column(db.DATETIME, default=datetime.datetime.now(), nullable=False, )  # comment='工单结束时间')
    applyreason = db.Column(db.String(254), nullable=False, default='', )  # comment='申请理由')
    status = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='最终状态,0未定义，1通过，2未通过，3通过后被回滚')

    def __repr__(self):
        return '<Workorder %r>' % self.id


# 流程表
class WorkFlow(db.Model):
    '''工作表'''
    __tablename__ = 'workflow'
    # 使用下面的配置进行解决
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    woid = db.Column(db.BigInteger, index=True, nullable=False, default=0, )  # comment='工单id')
    uid = db.Column(db.Integer, index=True, nullable=False, default=0, )  # comment='用户ID')
    uname = db.Column(db.String(20), nullable=False, default='', )  # comment='姓名')
    otime = db.Column(db.DATETIME, default=datetime.datetime.now(), nullable=False, )  # comment='操作时间')
    auditing = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='最终状态,0未定义，1同意，2拒绝')
    nowstep = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='当前走到了哪一步，0表示有问题的')
    maxstep = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='最大审批长度，0表示有问题的')

    def __repr__(self):
        return '<WorkFlow %r>' % self.woid


# goinception的记录表
class InceptionRecords(db.Model):
    '''工作表'''
    __tablename__ = 'inception_records'
    # 使用下面的配置进行解决
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False, default=0, )  # comment='用户ID')
    applydate = db.Column(db.DATE, default=datetime.datetime.today(), nullable=False, )  # comment='操作日期')
    applytime = db.Column(db.DATETIME, default=datetime.datetime.now(), nullable=False, )  # comment='操作时间')
    lastupdatetime = db.Column(db.DATETIME, default=datetime.datetime.now(), nullable=False, )  # comment='最后操作时间')
    sqltext = db.Column(db.Text, )  # comment='操作文本')
    filename = db.Column(db.String(128), nullable=False, default='', )  # comment='json文件名')
    sqlnums = db.Column(db.Integer, nullable=False, default=0, )  # comment='SQL语句数量')
    success_status = db.Column(db.Integer, nullable=False, default=0, )  # comment='是否成功通过审核')
    execute_status = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='通过后是否执行，0未执行，1已执行，2已回滚' ,9执行中)

    def __repr__(self):
        return '<InceptionRecords %r>' % self.id


# goinception执行的记录表
class InceptionRecordsExecute(db.Model):
    '''工作表'''
    __tablename__ = 'inception_records_execute'
    # 使用下面的配置进行解决
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    woid = db.Column(db.BigInteger, index=True, nullable=False, default=0, )  # comment='工单id')
    sequence = db.Column(db.String(50), index=True, nullable=False, default=0, )  # comment='执行的sql块信息')
    exetime = db.Column(db.DATETIME, default=datetime.datetime.now(), nullable=False, )  # comment='开始执行时间')
    sqltext = db.Column(db.Text, )  # comment='操作文本')
    affrows = db.Column(db.Integer, nullable=False, default=0, )  # comment='影响的行数')
    executetime = db.Column(db.FLOAT, nullable=False, default=0.0, )  # comment='耗时多少秒')
    exstatus = db.Column(db.String(64), nullable=False, default=0, )  # comment='执行状态'
    extype = db.Column(db.SmallInteger, nullable=False, default=0, )  # comment='操作类型:1，执行 2，回滚')
    opid_time = db.Column(db.String(50), nullable=False, default='', )
    backup_dbname = db.Column(db.String(64), nullable=False, default='', )

    def __repr__(self):
        return '<InceptionRecordsExecute %r>' % self.id


# 回滚表
class RollBack(db.Model):
    """
    回滚
    """
    __tablename__ = 'rollback'
    # 使用下面的配置进行解决
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    woid = db.Column(db.BigInteger, index=True, nullable=False, default=0, )  # comment='工单id')
    opid_time = db.Column(db.Integer, index=True, nullable=False, default=0, )  # comment='opid_time')
    sqltext = db.Column(db.String(5000), )  # comment='执行语句')
    tablename = db.Column(db.String(200), nullable=False)  # comment = '实例名称'
    dbname = db.Column(db.String(20), nullable=False, default='', )  # 数据库名
    host = db.Column(db.String(50), nullable=False)  # comment = '实例连接ip'
    create_time = db.Column(db.DATETIME, nullable=False, default=datetime.datetime.now())  # comment = '生成时间'


class QueryHistory(db.Model):
    """
    查询历史
    """
    __tablename__ = 'queryhistory'
    # 使用下面的配置进行解决
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, index=True, nullable=False, default=0, )  # comment='操作人id')
    name = db.Column(db.String(20), nullable=False, default='', )  # 操作人姓名
    dbname = db.Column(db.String(20), nullable=False, default='', )  # 数据库名
    sqltext = db.Column(db.String(5000), )  # comment='执行语句')
    select_env = db.Column(db.String(200), nullable=False)  # comment = '实例名称'
    host = db.Column(db.String(50), nullable=False)  # comment = '实例连接ip'
    create_time = db.Column(db.DATETIME, nullable=False, default=datetime.datetime.now())  # comment = '执行时间'

# -*- coding:utf8 -*-
import re

from flask import Flask

from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy
from flask_sqlalchemy import _SignallingSession as BaseSignallingSession
from flask_sqlalchemy import orm, partial, get_state

from datetime import datetime

class BindingKeyPattern(object):
    def __init__(self, pattern):
        self.raw_pattern = pattern
        self.compiled_pattern = re.compile(pattern)

    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self.raw_pattern)

    def match(self, key):
        return self.compiled_pattern.match(key)


class _BoundSection(object):
    def __init__(self, db_session_cls, name):
        self.db_session = db_session_cls()
        self.name = name

    def __enter__(self):
        self.db_session.push_binding(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_session.pop_binding()
        self.db_session.close()


class _SignallingSession(BaseSignallingSession):
    def __init__(self, *args, **kwargs):
        BaseSignallingSession.__init__(self, *args, **kwargs)
        self._binding_keys = []
        self._binding_key = None

    def push_binding(self, key):
        self._binding_keys.append(self._binding_key)
        self._binding_key = key

    def pop_binding(self):
        self._binding_key = self._binding_keys.pop()

    def get_bind(self, mapper, clause=None):
        binding_key = self.__find_binding_key(mapper)
        if binding_key is None:
            return BaseSignallingSession.get_bind(self, mapper, clause)
        else:
            state = get_state(self.app)
            return state.db.get_engine(self.app, bind=binding_key)

    def __find_binding_key(self, mapper):
        if mapper is None: # 맵퍼 없음
            return self._binding_key
        else:
            mapper_info = getattr(mapper.mapped_table, 'info', {})
            mapped_binding_key = mapper_info.get('bind_key')
            if mapped_binding_key: # 맵핑된 바인딩 키 존재
                if type(mapped_binding_key) is str: # 정적 바인딩
                    return mapped_binding_key
                else: # 동적 바인딩
                    if mapped_binding_key.match(self._binding_key): # 현재 바인딩
                        return self._binding_key
                    else: # 푸쉬된 바인딩
                        for pushed_binding_key in reversed(self._binding_keys):
                            if pushed_binding_key and mapped_binding_key.match(pushed_binding_key):
                                return pushed_binding_key
                        else:
                            raise Exception('NOT_FOUND_MAPPED_BINDING:%s CURRENT_BINDING:%s PUSHED_BINDINGS:%s' % (repr(mapped_binding_key), repr(self._binding_key), repr(self._binding_keys[1:])))
            else: # 맵핑된 바인딩 키가 없으면 디폴트 바인딩
                return self._binding_key


class SQLAlchemy(BaseSQLAlchemy):
    def bind(self, key):
        return _BoundSection(self.session, key)

    def create_scoped_session(self, options=None):
        """Helper factory method that creates a scoped session."""
        if options is None:
            options = {}
        scopefunc=options.pop('scopefunc', None)
        return orm.scoped_session(
            partial(_SignallingSession, self, **options), scopefunc=scopefunc
        )

    def get_binds(self, app=None):
        retval = BaseSQLAlchemy.get_binds(self, app)
       
        # get the binds for None again in order to make sure that 
        # it is the default bind for tables without an explicit bind 
        bind = None
        engine = self.get_engine(app, bind)
        tables = self.get_tables_for_bind(bind)
        retval.update(dict((table, engine) for table in tables))
        return retval

    def get_tables_for_bind(self, bind=None):
        """
        Returns a list of all tables relevant for a bind.
        Tables without an explicit __bind_key__ will be bound to all binds.
        """
        result = []
        for table in self.Model.metadata.tables.itervalues():
            table_bind_key = table.info.get('bind_key')
            if table_bind_key == bind:
                result.append(table)
            else:
                if bind:
                    if type(table_bind_key) is BindingKeyPattern and table_bind_key.match(bind):
                        result.append(table)
                    elif type(table_bind_key) is str and table_bind_key == bind:
                        result.append(table)

        return result


app = Flask(__name__)
db = SQLAlchemy(app)

class Notice(db.Model):
    __bind_key__ = 'globaldb'

    id = db.Column(db.Integer, primary_key=True)
    msg = db.Column(db.String, nullable=False)
    ctime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

class User(db.Model):
    __bind_key__ = BindingKeyPattern('[^_]+_userdb')

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), unique=True)

    login_logs = db.relationship(lambda: LoginLog, backref='owner')


class LoginLog(db.Model):
    __bind_key__ = BindingKeyPattern('[^_]+_logdb')

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    ctime = db.Column(db.DateTime, default=datetime.now(), nullable=False)


if __name__ == '__main__':
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_BINDS'] = {
        'globaldb': 'sqlite:///./global.db',
        'master_userdb': 'sqlite:///./master_user.db',
        'slave_userdb': 'sqlite:///./slave_user.db',
        'master_logdb':  'sqlite:///./master_log.db', 
        'slave_logdb':  'sqlite:///./slave_log.db', 
    }
        
    db.drop_all()
    db.create_all()

    notice = Notice(msg='NOTICE1')
    db.session.add(notice)
    db.session.commit()

    with db.bind('master_userdb'):
        notice = Notice(msg='NOTICE2')
        db.session.add(notice)
        db.session.commit()

        user = User(nickname='jaru')
        db.session.add(user)
        db.session.commit()

        with db.bind('master_logdb'):
            notice = Notice(msg='NOTICE3')
            db.session.add(notice)
            db.session.commit()

            login_log = LoginLog(owner=user)
            db.session.add(login_log)
            db.session.commit()
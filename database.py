from flask_sqlalchemy import SQLAlchemy as BaseSQLAlchemy
from flask_sqlalchemy import _SignallingSession as BaseSignallingSession
from flask_sqlalchemy import orm, partial, get_state

import re

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
        self._names = []
        self._name = None

    def push_binding(self, name):
        self._names.append(self._name)
        self._name = name

    def pop_binding(self):
        self._name = self._names.pop()

    def get_bind(self, mapper, clause=None):
        if mapper is None:
            bind_key = self._name
        else:
            if self._name is None:
                info = getattr(mapper.mapped_table, 'info' , {})
                bind_key = info.get('bind_key')
            else:
                bind_key = self._name

        if bind_key is None:
            return BaseSignallingSession.get_bind(self, mapper, clause)
        else:
            state = get_state(self.app)
            return state.db.get_engine(self.app, bind=bind_key)


class SQLAlchemy(BaseSQLAlchemy):
    def bind_key(self, name):
        return _BoundSection(self.session, name)

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
            if bind and re.match(table.info.get('bind_key'), bind):
                result.append(table)
        return result


if __name__ == '__main__':
    import os

    from flask import Flask

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_BINDS'] = {
        'data_1': 'sqlite:///./temp/test/data_1.db',
        'data_2': 'sqlite:///./temp/test/data_2.db',
        'log':  'sqlite:///./temp/test/log.db'
    }

    db = SQLAlchemy(app)

    class User(db.Model):
        __bind_key__ = 'data_\d'

        id = db.Column(db.Integer, primary_key=True)
        nickname = db.Column(db.String(64), index=True, unique=True)

        def __repr__(self):
            return "<User nickname='%s'>" % (self.nickname)

    class UserLog(db.Model):
        __bind_key__ = 'log'

        id = db.Column(db.Integer, primary_key=True)
        msg = db.Column(db.String(64))

    if not os.access('temp/test', os.R_OK):
        os.makedirs('temp/test')

    db.drop_all()
    db.create_all()

    with db.bind_key('data_1'):
        user = User(nickname='a')
        db.session.add(user)
        db.session.commit()

    with db.bind_key('data_2'):
        user = User(nickname='b')
        db.session.add(user)
        db.session.commit()

    user_log = UserLog(msg='x')
    db.session.add(user_log)
    db.session.commit()

    with db.bind_key('data_1'):
        print User.query.all()

    with db.bind_key('data_2'):
        print User.query.all()


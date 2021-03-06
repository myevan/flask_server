from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
db = SQLAlchemy(app)

class User(db.Model):
    __bind_key__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(80), unique=True)

    login_logs = db.relationship(lambda: LoginLog, backref='owner')


class LoginLog(db.Model):
    __bind_key__ = 'log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    ctime = db.Column(db.DateTime, default=datetime.now(), nullable=False)

if __name__ == '__main__':
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_BINDS'] = {
        'user': 'sqlite:///./user.db',
        'log':  'sqlite:///./log.db', 
    }
        
    db.drop_all()
    db.create_all()

    user = User(nickname='jaru')
    db.session.add(user)
    db.session.commit()

    login_log = LoginLog(owner=user)
    db.session.add(login_log)
    db.session.commit()

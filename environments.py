# -*- coding:utf8 -*-
import os
import yaml
import logging

from logging.handlers import RotatingFileHandler


class Environments(object):
    SQLITE_SCHEMA = 'sqlite:///'
    SQLITE_URI_MEMORY = 'sqlite:///:memory:'

    def __init__(self, app, project_dir_path):
        print project_dir_path
        self.app = app
        self.app.config['DEBUG'] = True
        self.app.config['PROJECT_DIR_PATH'] = project_dir_path

        log_dir_path = os.path.join(project_dir_path, './var/log')
        self.app.config['LOG_DEBUG_FILE_PATH'] = self.get_log_abs_path(log_dir_path, "APP_debug.log")
        self.app.config['LOG_DEBUG_FILE_MAX_MB_SIZE'] = 100
        self.app.config['LOG_DEBUG_BACKUP_COUNT'] = 2

        self.app.config['LOG_INFO_FILE_PATH'] = self.get_log_abs_path(log_dir_path, "APP_info.log")
        self.app.config['LOG_INFO_FILE_MAX_MB_SIZE'] = 100
        self.app.config['LOG_INFO_BACKUP_COUNT'] = 2

        self.app.config['LOG_ERROR_FILE_PATH'] = self.get_log_abs_path(log_dir_path, "APP_error.log")
        self.app.config['LOG_ERROR_FILE_MAX_MB_SIZE'] = 100
        self.app.config['LOG_ERROR_BACKUP_COUNT'] = 2

        self.app.config['LOG_FORMAT'] = "%(asctime)-15s %(message)s"

        data_dir_path = os.path.join(project_dir_path, '/var/data')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = self.SQLITE_URI_MEMORY
        self.app.config['SQLALCHEMY_BINDS'] = {} 
        self.app.config['SQLALCHEMY_ECHO'] = True

        self.log_formatter = None

    def __repr__(self):
        return '#### environments\n%s' % '\n'.join('* %s: %s' % (key, value) for key, value in self.app.config.items())

    @property
    def project_dir_path(self):
        "프로젝트 디렉토리 경로"
        return self.app.config['PROJECT_DIR_PATH']

    def get_sqlite_uri(self, data_dir_path, data_rel_path):
        "SQLite 주소를 얻는다"
        return self.SQLITE_SCHEMA + self.get_abs_path(os.path.join(data_dir_path, data_rel_path))

    def get_log_abs_path(self, log_dir_path, log_rel_path):
        "로그 절대 경로를 얻는다"
        return self.get_abs_path(os.path.join(log_dir_path, log_rel_path))

    def get_abs_path(self, rel_path):
        "상대 경로로 절대 경로를 얻는다"
        return os.path.normpath(os.path.join(self.project_dir_path, rel_path))

    def load_config_file(self, config_file_path):
        "설정 파일을 불러온다"
        try:
            with open(config_file_path) as config_file:
                self.load_config_dict(yaml.load(config_file))
        except IOError as e:
            print('Solution:')
            print('\tcp configs/template.yml %s' % config_file_path)
            print('')
            raise

    def load_config_dict(self, config_dict):
        "설정 사전을 불러온다"
        if config_dict:
            self.app.config.update(config_dict)

    def make_logs(self):
        "로그 파일을 생성한다"

        self._make_log_formatter()
        self._make_debug_log()
        self._make_error_log()
        self._make_info_log()

        self.__prepare_sqlalchemy_database(self.app.config['SQLALCHEMY_DATABASE_URI'])

        for bind_uri in self.app.config['SQLALCHEMY_BINDS'].values():
            self.__prepare_sqlalchemy_database(bind_uri)

    def _make_log_formatter(self):
        self.log_formatter = logging.Formatter(self.app.config['LOG_FORMAT'])

    def _make_debug_log(self):
        if self.app.config['DEBUG']:
            self.__make_log_file(
                logging.DEBUG,
                self.app.config['LOG_DEBUG_FILE_PATH'],
                log_max_mb_size=self.app.config['LOG_DEBUG_FILE_MAX_MB_SIZE'],
                log_bak_count=self.app.config['LOG_DEBUG_BACKUP_COUNT'])

    def _make_info_log(self):
        self.__make_log_file(
            logging.INFO,
            self.app.config['LOG_INFO_FILE_PATH'],
            log_max_mb_size=self.app.config['LOG_INFO_FILE_MAX_MB_SIZE'],
            log_bak_count=self.app.config['LOG_INFO_BACKUP_COUNT'])

    def _make_error_log(self):
        self.__make_log_file(
            logging.ERROR,
            self.app.config['LOG_ERROR_FILE_PATH'],
            log_max_mb_size=self.app.config['LOG_ERROR_FILE_MAX_MB_SIZE'],
            log_bak_count=self.app.config['LOG_ERROR_BACKUP_COUNT'])

    def __make_log_file(
            self, log_level, log_file_path, log_max_mb_size, log_bak_count):

        log_dir_path, log_file_name = os.path.split(log_file_path)
        if not os.access(log_dir_path, os.W_OK):
            os.makedirs(log_dir_path)

        log_file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=log_max_mb_size * 1024 * 1024,
            backupCount=log_bak_count)

        log_file_handler.setLevel(log_level)

        if self.log_formatter:
            log_file_handler.setFormatter(self.log_formatter)

        self.app.logger.addHandler(log_file_handler)

    @classmethod
    def __prepare_sqlalchemy_database(cls, db_uri):
        if db_uri.startswith(cls.SQLITE_SCHEMA):
            data_dir_path, data_file_path = os.path.split(db_uri[len(cls.SQLITE_SCHEMA):])
            if data_file_path == ':memory:':
                return

            if not os.access(data_dir_path, os.R_OK):
                os.makedirs(data_dir_path)

if __name__ == '__main__':
    from flask import Flask

    app = Flask(__name__)
    env = Environments(app, os.path.dirname(os.path.realpath(__file__)))
    #env.load_config_file(env.get_abs_path('config/builtin.yml'))
    print repr(env)

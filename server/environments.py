# -*- coding:utf8 -*-
import os
import yaml
import logging

from logging.handlers import RotatingFileHandler


class Environments(object):
    SQLITE_SCHEMA = 'sqlite:///'
    SQLITE_URI_MEMORY = 'sqlite:///:memory:'

    def __init__(self, app, server_dir_path):
        project_dir_path = os.path.dirname(server_dir_path)
        temp_dir_path = os.path.join(project_dir_path, 'TEMP')

        self.app = app
        self.app.config['DEBUG'] = True
        self.app.config['PROJECT_DIR_PATH'] = project_dir_path
        self.app.config['TEMP_DIR_PATH'] = temp_dir_path

        self.app.config['LOG_DEBUG_FILE_PATH'] = os.path.join(temp_dir_path, "APP_debug.log")
        self.app.config['LOG_DEBUG_FILE_MAX_MB_SIZE'] = 100
        self.app.config['LOG_DEBUG_BACKUP_COUNT'] = 2

        self.app.config['LOG_INFO_FILE_PATH'] = os.path.join(temp_dir_path, "APP_info.log")
        self.app.config['LOG_INFO_FILE_MAX_MB_SIZE'] = 100
        self.app.config['LOG_INFO_BACKUP_COUNT'] = 2

        self.app.config['LOG_ERROR_FILE_PATH'] = os.path.join(temp_dir_path, "APP_error.log")
        self.app.config['LOG_ERROR_FILE_MAX_MB_SIZE'] = 100
        self.app.config['LOG_ERROR_BACKUP_COUNT'] = 2

        self.app.config['LOG_FORMAT'] = "%(asctime)-15s %(message)s"

        self.app.config['SQLALCHEMY_DATABASE_URI'] = self.SQLITE_URI_MEMORY
        self.app.config['SQLALCHEMY_BINDS'] = {} 
        self.app.config['SQLALCHEMY_ECHO'] = True

        self.log_formatter = None

    def __repr__(self):
        return '#### environments\n%s' % '\n'.join(sorted('* %s: %s' % (key, value) for key, value in self.app.config.items()))

    @property
    def project_dir_path(self):
        "프로젝트 디렉토리 경로"
        return self.app.config['PROJECT_DIR_PATH']

    @property
    def temp_dir_path(self):
        "임시 디렉토리 경로"
        return self.app.config['TEMP_DIR_PATH']

    def get_sqlite_uri(self, data_dir_path, data_rel_path):
        "SQLite 주소를 얻는다"
        return self.SQLITE_SCHEMA + self.get_abs_path(os.path.join(data_dir_path, data_rel_path))

    def load_config_file(self, config_file_path):
        "설정 파일을 불러온다"

        try:
            with self._open_file(config_file_path) as config_file:
                self.load_config_dict(yaml.load(config_file))
        except IOError as e:
            print('Solution:')
            print('\tcp configs/template.yml %s' % config_file_path)
            print('')
            raise

    def load_config_dict(self, config_dict):
        "설정 사전을 불러온다"
        if config_dict:
            for config_key, config_value in config_dict.iteritems():
                if config_key == 'SQLALCHEMY_DATABASE_URI':
                    if config_value.startswith(self.SQLITE_SCHEMA): # SQLITE uri 경로를 실제 경로로 변경
                        self.app.config[config_key] = self.SQLITE_SCHEMA + os.path.realpath(config_value[len(self.SQLITE_SCHEMA):])
                elif config_key == 'SQLALCHEMY_BINDS': # SQLITE uri 경로를 실제 경로로 변경
                    self.app.config[config_key] = dict((bind_key, self.SQLITE_SCHEMA + os.path.realpath(bind_value[len(self.SQLITE_SCHEMA):])) for bind_key, bind_value in config_value)
                else:
                    self.app.config[config_key] = config_value

    def prepare_all(self):
        "모든 환경을 준비한다"

        self._prepare_log_formatter()
        self._prepare_debug_log()
        self._prepare_error_log()
        self._prepare_info_log()

        self._prepare_sqlalchemy_database(self.app.config['SQLALCHEMY_DATABASE_URI'])

        for bind_uri in self.app.config['SQLALCHEMY_BINDS'].values():
            self._prepare_sqlalchemy_database(bind_uri)

    def _open_file(self, file_path, *args, **kwargs):
        file_real_path = os.path.realpath(file_path)
        return open(file_real_path, *args, **kwargs)

    def _make_directory(self, dir_path):
        dir_real_path = os.path.realpath(dir_path)
        if dir_real_path == '/Users/jaru/MoonrabbitProjects/temp':
            raise Exception('!!')

        if not os.access(dir_real_path, os.R_OK):
            os.makedirs(dir_real_path)

    def _prepare_log_formatter(self):
        self.log_formatter = logging.Formatter(self.app.config['LOG_FORMAT'])

    def _prepare_debug_log(self):
        if self.app.config['DEBUG']:
            self.__prepare_log_file(
                logging.DEBUG,
                self.app.config['LOG_DEBUG_FILE_PATH'],
                log_max_mb_size=self.app.config['LOG_DEBUG_FILE_MAX_MB_SIZE'],
                log_bak_count=self.app.config['LOG_DEBUG_BACKUP_COUNT'])

    def _prepare_info_log(self):
        self.__prepare_log_file(
            logging.INFO,
            self.app.config['LOG_INFO_FILE_PATH'],
            log_max_mb_size=self.app.config['LOG_INFO_FILE_MAX_MB_SIZE'],
            log_bak_count=self.app.config['LOG_INFO_BACKUP_COUNT'])

    def _prepare_error_log(self):
        self.__prepare_log_file(
            logging.ERROR,
            self.app.config['LOG_ERROR_FILE_PATH'],
            log_max_mb_size=self.app.config['LOG_ERROR_FILE_MAX_MB_SIZE'],
            log_bak_count=self.app.config['LOG_ERROR_BACKUP_COUNT'])

    def __prepare_log_file(
            self, log_level, log_file_path, log_max_mb_size, log_bak_count):

        log_dir_path, log_file_name = os.path.split(log_file_path)
        self._make_directory(log_dir_path)

        log_file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=log_max_mb_size * 1024 * 1024,
            backupCount=log_bak_count)

        log_file_handler.setLevel(log_level)

        if self.log_formatter:
            log_file_handler.setFormatter(self.log_formatter)

        self.app.logger.addHandler(log_file_handler)

    def _prepare_sqlalchemy_database(self, db_uri):
        if db_uri.startswith(self.SQLITE_SCHEMA):
            data_dir_path, data_file_path = os.path.split(db_uri[len(self.SQLITE_SCHEMA):])
            if data_file_path == ':memory:':
                return
            
            self._make_directory(data_dir_path)

if __name__ == '__main__':
    from flask import Flask

    app = Flask(__name__)
    env = Environments(app, os.path.dirname(os.path.realpath(__file__)))
    #env.load_config_file(env.convert_abs_path('config/builtin.yml'))
    print repr(env)

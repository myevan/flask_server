#!/usr/bin/env python
# -*- coding:utf8 -*-
import os
import sys
import code
import argparse

def exec_command_line(exe_path, args):
    cmd_line = '%s %s' % (exe_path, ' '.join(args))
    print cmd_line
    return os.system(cmd_line)

try:
    import blog

    from framework import app, env, db

except ImportError as e:
    venv_dir_path = os.environ.get('VIRTUAL_ENV', None)
    if venv_dir_path is None:
        print(e)
        print('')

        workon_home_dir_path = os.environ.get('WORKON_HOME', None)
        if workon_home_dir_path is None:
            print('\t$ sudo pip install virtualenvwrapper')
            print('')
            print('\t$ vim ~/.bash_profile')
            print('\texport WORKON_HOME=~/VIRTUAL_ENVIRONEMNT_ROOT')
            print('\tsource /usr/local/bin/virtualenvwrapper.sh')
            sys.exit(-1)
        else:
            print('make virtual environment')
            print('\t$ mkvirtualenv [VIRTUAL_ENV_NAME]')
            print('')
            print('or work on virtual environment')
            print('\t$ workon [VIRTUAL_ENV_NAME]')
            sys.exit(-2)
    else:
        print('install requirements')
        print('\t$ pip install -r requirements.txt')

def install_package(ns):
    if not ns.package_names:
        print 'NO_SOURCE_PATH'
        return -101

    for package_name in ns.package_names:
        exec_command_line(EXE_VENV_PIP, ['install', package_name])

    exec_command_line(EXE_VENV_PIP, ['freeze', '> requirements.txt'])

def run_script(ns):
    if not ns.source_paths:
        print 'NO_SOURCE_PATH'
        return -101

    env.load_config_file('./config/flask/blog.yml')

    for source_path in ns.source_paths:
        execfile(ns.source_path, globals())

def run_shell(ns):
    env.load_config_file('./config/flask/blog.yml')
       
    code.interact('SHELL', local=dict(app=app, env=env, db=db))

def run_server(ns):
    env.load_config_file('./config/flask/blog.yml')

    db.drop_all()
    db.create_all()

    app.register_blueprint(blog.bp)
    app.run('0.0.0.0', port=ns.port)


def main(program_path, program_args):
    main_parser = argparse.ArgumentParser()
    sub_parsers = main_parser.add_subparsers()

    install_package_parser = sub_parsers.add_parser('install_package')
    install_package_parser.add_argument('package_names', type=str, nargs='+', help='package names')
    install_package_parser.set_defaults(func=install_package)

    run_script_parser = sub_parsers.add_parser('run_script')
    run_script_parser.add_argument('source_paths', type=str, nargs='+', help='python source path') 
    run_script_parser.set_defaults(func=run_script)

    run_server_parser = sub_parsers.add_parser('run_server')
    run_server_parser.add_argument('-P', '--port', type=int, default=5000, help='port') 
    run_server_parser.set_defaults(func=run_server)


    run_shell_parser = sub_parsers.add_parser('run_shell')
    run_shell_parser.set_defaults(func=run_shell)

    if program_args is None or len(program_args) == 0:
        main_parser.print_help()
        return -1

    ns = main_parser.parse_args(program_args)
    return ns.func(ns)

if __name__ == '__main__':
    import sys
    main(sys.argv[0], sys.argv[1:])

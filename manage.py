#!/usr/bin/env python
import os
import code
import argparse

import blog

from framework import app, env, db

def run_script(ns):
    if not ns.source_path:
        print 'NO_SOURCE_PATH'
        return -101

    env.load_config_file('./config/flask/blog.yml')

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

    server_parser = sub_parsers.add_parser('server')
    server_parser.add_argument('-P', '--port', type=int, default=5000, help='port') 
    server_parser.set_defaults(func=run_server)

    script_parser = sub_parsers.add_parser('script')
    script_parser.add_argument('-S', '--source-path', type=str, help='python source path') 
    script_parser.set_defaults(func=run_script)

    shell_parser = sub_parsers.add_parser('shell')
    #shell_parser.add_argument('--config', action='store', help='config path') 
    shell_parser.set_defaults(func=run_shell)

    if program_args is None or len(program_args) == 0:
        main_parser.print_help()
        return -1

    ns = main_parser.parse_args(program_args)
    return ns.func(ns)

if __name__ == '__main__':
    import sys
    main(sys.argv[0], sys.argv[1:])

#!/usr/bin/env python
import os
import code
import argparse

from framework import app, env

def run_shell(ns):
    code.interact('SHELL', local=dict(app=app, env=env))

def run_server(ns):
    app.run('0.0.0.0', port=ns.port)

def main(program_path, program_args):
    main_parser = argparse.ArgumentParser()
    sub_parsers = main_parser.add_subparsers()

    server_parser = sub_parsers.add_parser('server')
    server_parser.add_argument('--port', type=int, default=5000, help='port') 
    server_parser.set_defaults(func=run_server)

    shell_parser = sub_parsers.add_parser('shell')
    #shell_parser.add_argument('--config', action='store', help='config path') 
    shell_parser.set_defaults(func=run_shell)

    if program_args is None or len(program_args) == 0:
        main_parser.print_help()
        return -1

    command_namespace = main_parser.parse_args(program_args)
    command_namespace.func(command_namespace)

if __name__ == '__main__':
    import sys
    main(sys.argv[0], sys.argv[1:])

#!/usr/bin/env python

import click
from multiprocessing import Pool
import logging
from config import Config, cf

logger = logging.getLogger('networkmetrix')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(eval('logging.{}'.format(cf.log_level)))

from database import db
from node import Node


# Initialize clients
node = {ip: Node(client_conf) for ip, client_conf in cf.client.iteritems()}


# Wrappers for Pool
def upload_wrapper(node):
    node.upload()

def execute_wrapper(node):
    node.execute()

def upexec_wrapper(node):
    node.upload()
    node.execute()


# Command line parsing
@click.group()
def program():
    """ Type 'server.py <Command>' to run specific command. """


def execute_remote_cmd(command, host):
    if host:
        try:
            command(node[host])
        except KeyError:
            raise click.BadParameter('Host not found in configuration')
        return

    p = Pool(cf.concurrency)
    p.map(command, node.values())


@click.command()
@click.option('--file', type=click.Path(exists=True),
              help='Use specific config file',
              metavar='file')
@click.option('-h', '--host', default='',
              help='Show config for specific host only', 
              metavar='host', show_default=True)
def config(file, host):
    """ Validate and print config """

    conf = Config(file) if file else cf
    if host:
        try:
            click.echo(conf.client[host])
        except KeyError:
            raise click.BadParameter('Host not found in configuration')
        return

    click.echo(conf)
 

@click.command()
@click.option('-h', '--host', default='', 
              help='Upload on specific host only', 
              metavar='host', show_default=True)
def upload(host):
    """ Upload client script to server(s) """
    execute_remote_cmd(upload_wrapper, host)
       

@click.command()
@click.option('-h', '--host', default='', 
              help='Execute on specific host only', 
              metavar='host', show_default=True)
def execute(host):
    """ Execute client script on server(s) """
    execute_remote_cmd(execute_wrapper, host)


@click.command()
@click.option('-h', '--host', default='', 
              help='Upload and execute on specific host only', 
              metavar='host', show_default=True)
def upexec(host):
    """ Upload and execute client script on server(s) """
    execute_remote_cmd(upexec_wrapper, host)


@click.command()
@click.option('-h', '--host', default='', 
              help='Show specific host only', 
              metavar='host', show_default=True)
@click.option('-l', '--limit', default=4,
              help='Limit number of returned rows',
              type=int, show_default=True)
def status(host, limit):
    """ Print latest machine(s) stats from db """

    sql = '''
SELECT * FROM `{}`
WHERE ip='{}'
ORDER BY ts DESC
LIMIT {}
'''

    if host:
        for row in db.fetchall(sql.format(db.table, host, limit)):
            click.echo(row)
        return

    for host in node.keys():
        click.echo('-' * 80)
        click.echo(host)
        for row in db.fetchall(sql.format(db.table, host, limit)):
            click.echo(row)


 

program.add_command(config)
program.add_command(execute)
program.add_command(upload)
program.add_command(status)
program.add_command(upexec)

if __name__ == '__main__':
    program()

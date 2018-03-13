# -*- coding: utf-8 -*-
import click
from tabulate import tabulate

from aiida.cmdline.utils.common import format_local_time
from aiida.daemon.client import DaemonClient


def print_client_response_status(response):
    """
    Print the response status of a call to the CircusClient through the DaemonClient

    :param response: the response object
    """
    if 'status' not in response:
        return

    if response['status'] == 'active':
        click.secho('RUNNING', fg='green', bold=True)
    elif response['status'] == DaemonClient.DAEMON_ERROR:
        click.secho('FAILED', fg='red', bold=True)
        click.echo('Try to run \'verdi daemon start --foreground\' to potentially see the exception')
    elif response['status'] == 'ok':
        click.secho('OK', fg='green', bold=True)
    else:
        click.echo(response['status'])


def get_daemon_status(client):
    """
    Print the status information of the daemon for a given profile through its DaemonClient

    :param client: the DaemonClient
    """

    if not client.is_daemon_running:
        return 'The daemon is not running'

    status_response = client.get_status()

    if status_response['status'] == 'stopped':
        return 'The daemon is paused'
    elif status_response['status'] == 'error':
        return 'The daemon is in an unexpected state, try verdi daemon restart --reset'

    worker_response = client.get_worker_info()
    daemon_response = client.get_daemon_info()

    workers = [['PID', 'MEM %', 'CPU %', 'started']]
    for worker_pid, worker_info in worker_response['info'].items():
        worker_row = [worker_pid, worker_info['mem'], worker_info['cpu'], format_local_time(worker_info['create_time'])]
        workers.append(worker_row)

    if len(workers) > 1:
        workers_info = tabulate(workers, headers='firstrow', tablefmt='simple')
    else:
        workers_info = '--> No workers are running. Use verdi daemon incr to start some!\n'

    info = {
        'pid': daemon_response['info']['pid'],
        'time': format_local_time(daemon_response['info']['create_time']),
        'nworkers': len(workers) - 1,
        'workers': workers_info
    }

    template = ('Daemon is running as PID {pid} since {time}\nActive workers [{nworkers}]:\n{workers}\n'
                'Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers')

    return template.format(**info)
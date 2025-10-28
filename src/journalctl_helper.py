import time
from datetime import datetime, timedelta

import allure

from tests.cyp_test_lib.helpers.os_helper import get_server_seconds_since_epoch, get_latest_pid
from tests.cyp_test_lib.ssh_client import SshClient


class JournalctlGrepException(BaseException):
    pass


@allure.step('Get journalctl output for {service_name} {delta_seconds} seconds ago')
def get_journalctl_output_with_delta_seconds(ssh_client: SshClient, service_name: str, delta_seconds: int, as_sudo: bool = True) -> str:
    if as_sudo:
        return ssh_client.exec_sudo(f'journalctl -t {service_name} -S "{delta_seconds} seconds ago"').stdout
    else:
        return ssh_client.exec(f'journalctl -t {service_name} -S "{delta_seconds} seconds ago"').stdout


@allure.step('Get journalctl output for {service_name} with pid {pid}')
def get_journalctl_output_for_pid(ssh_client: SshClient, service_name: str, pid: int, as_sudo: bool = True) -> str:
    if as_sudo:
        return ssh_client.exec_sudo(f'journalctl -t {service_name} _PID={pid}').stdout
    else:
        return ssh_client.exec(f'journalctl -t {service_name} _PID={pid}').stdout


@allure.step('Get journalctl records for latest pid')
def get_journalctl_for_latest_pid(ssh_client: SshClient, service_name: str, lines_count: int = None,
                                  as_sudo: bool = True) -> str:
    pid = get_latest_pid(ssh_client, service_name)
    if as_sudo:
        data = ssh_client.exec_sudo(f'journalctl -t {service_name} _PID={pid}').stdout
    else:
        data = ssh_client.exec(f'journalctl -t {service_name} _PID={pid}').stdout
    if lines_count and len(data.splitlines()) < lines_count:
        time.sleep(3)
        if as_sudo:
            data = ssh_client.exec_sudo(f'journalctl -t {service_name} _PID={pid}').stdout
        else:
            data = ssh_client.exec(f'journalctl -t {service_name} _PID={pid}').stdout
    return data


@allure.step('Grep journalctl records for latest pid')
def grep_journalctl_for_latest_pid(ssh_client: SshClient, service_name: str, substr: str, wait_sec: int = 1,
                                   accept_no_result: bool = False, ignore_case: bool = True, as_sudo: bool = True,
                                   sleep_sec: float = 0.2) -> str:
    timer = datetime.now() + timedelta(seconds=wait_sec)
    records = ''
    while datetime.now() < timer:
        records = get_journalctl_for_latest_pid(ssh_client, service_name, as_sudo=as_sudo)
        if ignore_case:
            records = records.lower()
            substr = substr.lower()
        if substr in records:
            return records
        time.sleep(sleep_sec)
    if accept_no_result:
        return ''
    raise JournalctlGrepException(f'Failed to find "{substr}" within {wait_sec} sec for {service_name}: {records}')


@allure.step('Grep journalctl records for {substr}')
def grep_journalctl(ssh_client: SshClient, service_name: str, substr: str, date_start: int,
                    accept_no_result: bool = False, ignore_case: bool = True, as_sudo: bool = True) -> str:
    since_time = get_server_seconds_since_epoch(ssh_client) - date_start
    command = (f'journalctl -t {service_name} -S "{since_time} seconds ago" | '
               f'grep {"-i" if ignore_case else ""} "{substr}"')
    if as_sudo:
        output = ssh_client.exec_sudo(command, ignore_rc=True)
    else:
        output = ssh_client.exec(command, ignore_rc=True)
    if output.rc == 0 or accept_no_result:
        return output.stdout
    raise JournalctlGrepException(f'Failed to find matching to "{substr}" records since {since_time}: '
                                  f'rc={output.rc}, error={output.stderr}, stdout={output.stdout}')


@allure.step('Grep journalctl records for {substr} with wait')
def grep_journalctl_with_wait(ssh_client: SshClient, service_name: str, substr: str, date_start: int, wait_sec: int = 4,
                              accept_no_result: bool = False, ignore_case: bool = True, as_sudo: bool = True,
                              sleep_sec: float = 0.5) -> str:
    timer = datetime.now() + timedelta(0, wait_sec)
    exception = None
    while datetime.now() < timer:
        try:
            return grep_journalctl(ssh_client, service_name, substr, date_start, accept_no_result=False,
                                   ignore_case=ignore_case, as_sudo=as_sudo)
        except JournalctlGrepException as exc:
            exception = exc
            time.sleep(sleep_sec)
    if accept_no_result:
        return ''
    raise exception

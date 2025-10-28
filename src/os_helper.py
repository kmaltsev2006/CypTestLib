import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

import allure

from tests.cyp_test_lib.constants.paths import BACKUP_SUFFIX
from tests.cyp_test_lib.constants.services import SERVICE_RUN_CMD, CONFIG_INDICATOR_CMD
from tests.cyp_test_lib.helpers.randomization import rand_str
from tests.cyp_test_lib.models.build_info import CliBuildInfoModel
from tests.cyp_test_lib.ssh_client import SshClient
from tests.cyp_test_lib.systemd import Systemd


class GrepException(BaseException):
    pass


@allure.step('Check if file is present')
def is_file_present(ssh_client: SshClient, file_name: str) -> bool:
    result = ssh_client.exec_sudo(f'stat {file_name}', ignore_rc=True)
    return result.rc == 0


@allure.step('Count file lines')
def count_file_lines(ssh_client: SshClient, file_name: str) -> int:
    if is_file_present(ssh_client, file_name):
        return int(ssh_client.exec_sudo(f'wc -l {file_name}  |  awk \'{{ print $1 }}\'').stdout)
    else:
        raise RuntimeError(f'Failed to find {file_name}')


@allure.step('Grep {file_path} records for {substr}')
def grep_file(ssh_client: SshClient, substr: str, file_path: str, after_line: Optional[int] = None,
              accept_no_result: bool = False) -> str:
    lines_to_show = count_file_lines(ssh_client, file_path)
    if after_line:
        lines_to_show -= after_line
    command = f'tail -n {lines_to_show} {file_path} | grep "{substr}"'
    output = ssh_client.exec_sudo(command, ignore_rc=True)
    if output.rc == 0 or accept_no_result:
        return output.stdout
    raise GrepException(f'Failed to find matching to "{substr}" records for {lines_to_show} lines in '
                        f'{file_path}: rc={output.rc}, error={output.stderr}, stdout={output.stdout}')


def grep_file_with_wait(ssh_client: SshClient, substr: str, file_path: str, after_line: Optional[int] = None,
                        accept_no_result: bool = False, wait_sec: int = 4) -> str:
    with allure.step(f'Grep {file_path} and wait'):
        timer = datetime.now() + timedelta(0, wait_sec)
        exception = None
        while datetime.now() < timer:
            try:
                return grep_file(ssh_client, substr, file_path, after_line, accept_no_result=False)
            except GrepException as exc:
                exception = exc
                time.sleep(0.5)
        if accept_no_result:
            return ''
        raise exception


@allure.step('Get server seconds since epoch')
def get_server_seconds_since_epoch(ssh_client: SshClient) -> int:
    return int(ssh_client.exec_sudo('date +%s').stdout)


@allure.step('Get pid from systemd status')
def get_latest_pid(ssh_client: SshClient, service_name: str) -> int:
    status = Systemd.service_status(ssh_client, service_name, ignore_rc=True).stdout
    return int(status.split('Main PID: ')[1].split(' ')[0])


@allure.step('Add line to file')
def add_line_to_file(ssh_client: SshClient, line: str, filename: str, append_to_file: bool = True,
                     empty_line_cleanup: bool = True):
    if '"' in line:
        line = line.replace('"', '\\"')
    line = f'{line}\n'
    append = '>>' if append_to_file else '>'
    ssh_client.exec_sudo(f'echo "{line}" {append} {filename}', run_with_bash=True)
    if empty_line_cleanup:
        ssh_client.exec_sudo(f'sed -i \'/^$/d\' {filename}')


@contextmanager
def move_file(ssh_client: SshClient, filename: str, fail_if_absent: bool = True):
    if not is_file_present(ssh_client, filename):
        if fail_if_absent:
            raise FileNotFoundError(f'Failed to find {filename} to move')
        yield
    else:
        new_tmp_file = f'{filename}.tmp_removed'
        ssh_client.exec_sudo(f'mv -f {filename} {new_tmp_file}')
        try:
            yield
        finally:
            ssh_client.exec_sudo(f'mv -f {new_tmp_file} {filename}')


def get_service_build_info(ssh_client: SshClient, service_name: str) -> CliBuildInfoModel:
    if not get_service_build_info.info or service_name not in get_service_build_info.info:
        service_build_info = CliBuildInfoModel.parse_response(ssh_client.exec_sudo(f'{service_name} -b').stdout)
        get_service_build_info.info = {service_name: service_build_info}
    return get_service_build_info.info.get(service_name)


get_service_build_info.info = None


def make_backup(ssh_client: SshClient, file_name: str):
    with allure.step(f'Make backup of {file_name}'):
        ssh_client.exec_sudo(f'cp {file_name} {file_name}{BACKUP_SUFFIX}')


def restore_backup(ssh_client: SshClient, file_name: str):
    with allure.step(f'Restore backup of {file_name}'):
        ssh_client.exec_sudo(f'cp {file_name}{BACKUP_SUFFIX} {file_name}')


@allure.step('Add or update line in file')
def add_or_update_line_in_file(ssh_client: SshClient, filename: str, field: str, value: str, delimiter: str = '='):
    value = value.replace('/', '\\/')
    if grep_file(ssh_client, substr=field, file_path=filename, accept_no_result=True):
        ssh_client.exec_sudo(f'sed -i "s/^{field}.*$/{field}{delimiter}{value}/" {filename}')
    else:
        add_line_to_file(ssh_client, line=f'{field}{delimiter}{value}', filename=filename, append_to_file=True)


@allure.step('Get recent logs')
def get_recent_logs(ssh_client: SshClient, service_name: str, lines_to_check: int = 20) -> str:
    return ssh_client.exec_sudo(f'journalctl --unit {service_name} -n {lines_to_check}').stdout


@allure.step('Run service from cmd')
def run_service_from_console(ssh_client: SshClient, app_config_path: Optional[str], service_binary: str,
                             output_file: str = f'/tmp/service_{rand_str(6)}.txt', sdnotify_flag: bool = False) -> str:
    with allure.step('Chmod output file'):
        if not is_file_present(ssh_client, output_file):
            ssh_client.exec_sudo(f'touch {output_file}')
        ssh_client.exec_sudo(f'chmod 666 {output_file}')  # on TO file will not be accessible otherwise
    executable = service_binary.split('/')[-1]
    with_config = f'{CONFIG_INDICATOR_CMD[executable]} {app_config_path}' if app_config_path else ''
    with_sdnotify = '--enable-sdnotify' if sdnotify_flag else ''
    service_run_flag = f'{service_binary} {SERVICE_RUN_CMD[executable]}'
    ssh_client.exec_nohup_sudo(f'{service_run_flag} {with_sdnotify} {with_config} > {output_file} 2>&1 &')
    return output_file


def send_signals(ssh_client: SshClient, linux_signal: int, service_name: str, service_binary: str,
                 stdout_file: str = '/tmp/output', config_path: str = ''):
    run_cmd = f'{service_binary} run'
    if config_path:
        run_cmd += f' -c {config_path}'
    t_thread = threading.Thread(
        target=ssh_client.exec_sudo,
        args=(f'{run_cmd} > {stdout_file}',),
        kwargs={'ignore_rc': True}
    )
    t_thread.start()
    time.sleep(3)
    ssh_client.exec_sudo(f'pkill -{linux_signal} -f {service_name}', ignore_rc=True)
    t_thread.join()


@allure.step('Get service version')
def get_service_version(ssh_client: SshClient, service_name: str) -> str:
    return ssh_client.exec_sudo(f'{service_name} -v | grep -Po "(?<=^Version: ).+$"').stdout.strip()

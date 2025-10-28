import time

import allure
import pytest
from retrying import retry

from tests.cyp_test_lib.ssh_client import SshClient, SShResponse


class Systemd:

    @staticmethod
    def _verify_status(ssh_client: SshClient, service_name: str, target_status: str, timeout: int, sdnotify: bool = False):
        search = 'Status:' if sdnotify else 'Active:'
        for i in range(timeout):
            response = Systemd.service_status(ssh_client, service_name, True)
            status_line = [j.strip().lower() for j in response.stdout.splitlines() if search in j][0]
            status = status_line.split(maxsplit=1 if sdnotify else -1)[1]

            status_reached = target_status.lower() in status if sdnotify else status == target_status.lower()

            if status_reached:
                break
            if i >= timeout - 1:
                raise TimeoutError(f'After {i} seconds service {service_name} has not reached status "{target_status}".'
                                   f' Current status "{status}"')
            time.sleep(1)

    @staticmethod
    def service_enable(ssh_client: SshClient, service_name: str, ignore_rc: bool = False):
        allure.title(f'Enable {service_name} service')
        ssh_client.exec_sudo(cmd=f'systemctl enable {service_name}', ignore_rc=ignore_rc)

    @staticmethod
    def service_disable(ssh_client: SshClient, service_name: str, ignore_rc: bool = False):
        allure.title(f'Disable {service_name} service')
        ssh_client.exec_sudo(cmd=f'systemctl disable {service_name}', ignore_rc=ignore_rc)

    @staticmethod
    def daemon_reload(ssh_client: SshClient, ignore_rc: bool = False):
        allure.title('Daemon reload')
        ssh_client.exec_sudo(cmd='sudo systemctl daemon-reload', ignore_rc=ignore_rc)

    @staticmethod
    def reset_failed(ssh_client: SshClient, service_name: str, ignore_rc: bool = False):
        allure.title(f'Reset service {service_name} start failures')
        ssh_client.exec_sudo(cmd=f'systemctl reset-failed {service_name}', ignore_rc=ignore_rc)

    @staticmethod
    def service_is_active(ssh_client: SshClient, service_name: str, retries: int = 3):
        allure.title(f'Status of {service_name} service')
        active = False

        for _ in range(retries):
            res = ssh_client.exec_sudo(cmd=f'systemctl is-active {service_name}', ignore_rc=True)
            if res.stdout == 'active':
                active = True
                break
            time.sleep(1)

        if not active:
            pytest.fail(f'{service_name} service is inactive')

    @staticmethod
    def service_status(ssh_client: SshClient, service_name: str, ignore_rc: bool = False) -> SShResponse:
        allure.title(f'Status of {service_name} service')
        status = ssh_client.exec_sudo(cmd=f'systemctl status {service_name}', ignore_rc=ignore_rc)
        return status

    @staticmethod
    def service_start(ssh_client: SshClient, service_name: str, ignore_rc: bool = False, verify_status: bool = True,
                      target_status: str = 'active', timeout: int = 60, use_sdnotify: bool = False):
        allure.title(f'Start {service_name} service')
        ssh_client.exec_sudo(cmd=f'systemctl start {service_name}', ignore_rc=ignore_rc)
        if verify_status:
            Systemd._verify_status(ssh_client, service_name, target_status, timeout, use_sdnotify)

    @staticmethod
    def service_restart(ssh_client: SshClient, service_name: str, ignore_rc: bool = False, verify_status: bool = True,
                        target_status: str = 'active', timeout: int = 60, use_sdnotify: bool = False):
        allure.title(f'Restart {service_name} service')
        ssh_client.exec_sudo(cmd=f'systemctl restart {service_name}', ignore_rc=ignore_rc)
        if verify_status:
            Systemd._verify_status(ssh_client, service_name, target_status, timeout, use_sdnotify)

    @staticmethod
    def service_reload(ssh_client: SshClient, service_name: str, ignore_rc: bool = False, verify_status: bool = True,
                       target_status: str = 'active', timeout: int = 60, use_sdnotify: bool = False):
        allure.title(f'Reload {service_name} service')
        ssh_client.exec_sudo(cmd=f'systemctl reload {service_name}', ignore_rc=ignore_rc)
        if verify_status:
            Systemd._verify_status(ssh_client, service_name, target_status, timeout, use_sdnotify)

    @staticmethod
    def service_stop(ssh_client: SshClient, service_name: str, ignore_rc: bool = False):
        allure.title(f'Stop {service_name} service')
        ssh_client.exec_sudo(cmd=f'systemctl stop {service_name}', ignore_rc=ignore_rc)

    @staticmethod
    def get_service_sdnotify_status(ssh_client: SshClient, service_name: str) -> str:
        allure.title(f'Sdnotify status of {service_name} service')
        status = ssh_client.exec_sudo(cmd=f'systemctl status {service_name} | grep Status:', ignore_rc=True)
        if status.rc != 0:
            raise RuntimeError(f'Failed to obtain sdnotify "Status" from systemctl:\n'
                               f'{Systemd.service_status(ssh_client, service_name, ignore_rc=True)}')
        return status.stdout.split(':')[1].strip().replace('"', '')

    @staticmethod
    @retry(stop_max_attempt_number=4, wait_fixed=1000)
    def service_is_sdnotify_ready(ssh_client: SshClient, service_name: str):
        if Systemd.get_service_sdnotify_status(ssh_client, service_name) != 'service started successfully':
            pytest.fail(f'{service_name} service is not sdnotify ready:\n'
                        f'{Systemd.service_status(ssh_client, service_name, ignore_rc=True)}')

import os

from .env import get_env_from_file
from ..constants.paths import LOCAL_ENV_FILE
from ..ssh_client import SshClient


class RemoteTargetInfo:

    def __init__(self) -> None:
        env_data = get_env_from_file(LOCAL_ENV_FILE)
        self.client = SshClient(
            host=env_data['TARGET'] if env_data else os.getenv('TARGET'),
            port=env_data['TARGET_SSH_PORT'] if env_data else os.getenv('TARGET_SSH_PORT'),
            user=env_data['TARGET_USER'] if env_data else os.getenv('TARGET_USER'),
            password=env_data['TARGET_PASSWORD'] if env_data else os.getenv('TARGET_PASSWORD')
        )
        self.client.connect()

    def target_kernel(self) -> str:
        return self.client.exec('uname -r').stdout

    def is_virtual(self) -> bool:
        vm = False
        data = self.client.exec('hostnamectl| grep Chassis', ignore_rc=True)
        if 'vm' in data.stdout:
            vm = True
        return vm

    def is_qemu(self) -> bool:
        qemu = False
        data = self.client.exec('hostnamectl| grep Vendor', ignore_rc=True)
        if 'QEMU' in data.stdout:
            qemu = True
        return qemu

    def is_dns_enable(self) -> bool:
        is_enabled = True
        data = self.client.exec('ping -c 3 rpmfind.net', ignore_rc=True)
        if 'Temporary failure in name resolution' in data.stderr:
            is_enabled = False
        return is_enabled

import logging
import os
import tempfile
from contextlib import suppress
from dataclasses import dataclass

import allure
import paramiko
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

from tests.cyp_test_lib.helpers.randomization import rand_str

LOGGER = logging.getLogger(__name__)
TMP_REMOTE_PATH = '/tmp'


@dataclass
class SShResponse:
    stdout: str
    stderr: str
    rc: int


class UnexpectedSshResponseException(Exception):
    def __init__(self, message, ssh_response: SShResponse):
        message += f'\nOutput: {ssh_response.stdout}\nError: {ssh_response.stderr}'
        super().__init__(message)
        self.ssh_response = ssh_response


class SshClient:

    def __init__(self, user: str, password: str, host: str, port: str, **kwargs):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.client = SSHClient()
        self.connect_kwargs = kwargs
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.safe_password = "'" + self.password.replace("'", "'\\''") + "'"

    def connect(self):
        # This block ensures backward compatibility with previous setup, where auth_timeout defaulted to 5 seconds
        if 'auth_timeout' not in self.connect_kwargs:
            self.connect_kwargs['auth_timeout'] = 5
        try:
            self.client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                port=int(self.port),
                **self.connect_kwargs,
            )
        except paramiko.ssh_exception.AuthenticationException as e:
            if not self.password:
                self.client.get_transport().auth_none(self.user)
            else:
                raise e

    # Execute command via ssh
    def exec(self, cmd: str, *args, expected_rc: int = 0, ignore_rc: bool = False, **kwargs) -> SShResponse:

        def _hide_password(cmd: str) -> str:
            log_cmd = cmd
            if 'sudo -S ' in log_cmd:
                if len(self.password) > 0:
                    log_cmd = log_cmd.replace(self.password, '*hidden*')
            return log_cmd

        log_cmd = _hide_password(cmd)
        LOGGER.info(f'Ssh command to run: {log_cmd}')
        _, stdout, stderr = self.client.exec_command(cmd, *args, **kwargs)

        # some tools provide binary output which cannot be decoded to utf-8
        try:
            out = stdout.read().decode('utf-8').strip('\n')
        except UnicodeDecodeError as e:
            LOGGER.error(f'Failed reading utf-8 stdout: {e}')
            out1 = stdout.read()
            out2 = e.object.decode('utf-8', 'ignore')
            out = out1 if out1 else out2
        try:
            err = stderr.read().decode('utf-8').strip('\n')
        except UnicodeDecodeError as e:
            LOGGER.error(f'Failed reading utf-8 stderr: {e}')
            err1 = stderr.read()
            err2 = e.object.decode('utf-8', 'ignore')
            err = err1 if err1 else err2
        rc = stdout.channel.recv_exit_status()
        LOGGER.debug(f'Ssh response: rc={rc}, err={err}, stdout={out}')

        # also hide password from output and error messages
        out = _hide_password(out)
        err = _hide_password(err)
        response = SShResponse(out, err, rc)
        if not ignore_rc:
            if rc != expected_rc:
                raise UnexpectedSshResponseException(
                    message=f'While executing "{log_cmd}" received {rc} exit code (expected {expected_rc})',
                    ssh_response=response
                )
        return response

    # Execute command via ssh with sudo
    def exec_sudo(self, cmd: str, *args, run_with_bash: bool = False, **kwargs) -> SShResponse:
        sudo_command = f'sudo -S bash -c \'{cmd}\'' if run_with_bash else f'sudo -S {cmd}'
        return self.exec(f'echo {self.safe_password} | {sudo_command}', *args, **kwargs)

    # Execute command via ssh with nohup and sudo
    def exec_nohup_sudo(self, cmd: str, *args, run_with_bash: bool = False, **kwargs) -> SShResponse:
        sudo_command = f'sudo -S bash -c \'{cmd}\'' if run_with_bash else f'sudo -S {cmd}'
        return self.exec(f'echo {self.safe_password} | nohup {sudo_command}', *args, **kwargs)

    def close(self):
        self.client.close()

    @allure.step('Get file via scp: {remote_path} → {local_path}')
    def get_file(self, remote_path: str, local_path: str):
        LOGGER.info(f'Copy file from remote {remote_path} to local {local_path}')
        client = SCPClient(self.client.get_transport())
        client.get(remote_path=remote_path, local_path=local_path)

    @allure.step('Put file via scp: {local_path} → {remote_path} (recursive={recursive})')
    def put_file(self, local_path: str, remote_path: str, recursive: bool = False):
        # be careful of Scp: PermissionDenied error if the file to be replaced lacks permissions for your account
        # see chmod workaround in put_file_sudo
        LOGGER.info(f'Copy file from local {local_path} to remote {remote_path}')
        client = SCPClient(self.client.get_transport())
        client.put(files=local_path, remote_path=remote_path, recursive=recursive)

    @allure.step('Put file via scp with sudo: {local_path} → {remote_path}')
    def put_file_sudo(self, local_path: str, remote_path: str, recursive: bool = False):
        # Unable to use os.path.join, because on windows it results in wrong path (like '/tmp\\file.yaml')
        tmp_remote_path = f'{TMP_REMOTE_PATH}/{rand_str(8)}'
        self.exec_sudo(f'mkdir {tmp_remote_path}')
        self.exec_sudo(f'chmod -R 777 {tmp_remote_path}')
        tmp_file_path = f'{tmp_remote_path}/{os.path.split(os.path.normpath(local_path))[1]}'
        self.put_file(local_path=os.path.normpath(local_path), remote_path=tmp_remote_path, recursive=recursive)
        self.exec_sudo(f'mv {tmp_file_path} {remote_path}')
        self.exec_sudo(f'rmdir {tmp_remote_path}')

    @allure.step('Create dir on the host: {host_dir}')
    def create_remote_dir(self, host_dir: str):
        with self.client.open_sftp() as sftp_client:
            with suppress(Exception):
                sftp_client.mkdir(host_dir)

    @allure.step('Remove dir from remote host: {host_dir}')
    def remove_dir_from_host(self, host_dir: str):
        with suppress(Exception):
            self.exec_sudo(f'rm -rf {host_dir}')

    @allure.step('Write text to remote file')
    def write_text_to_remote(self, text: str, remote_path: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_file = os.path.join(tmp_dir, f'{rand_str(length=8)}.txt')
            with open(local_file, 'wt', newline='\n') as fh:
                fh.write(text)
            self.put_file_sudo(local_file, remote_path)

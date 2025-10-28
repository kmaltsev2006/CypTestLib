import os

from tests.cyp_test_lib.ssh_client import SshClient, SShResponse


class RemoteActions:

    def __init__(self) -> None:
        self.client = SshClient(
            host=os.getenv('TARGET'),
            port=os.getenv('TARGET_PORT'),
            user=os.getenv('TARGET_USER'),
            password=os.getenv('TARGET_PASSWORD')
        )
        self.client.connect()

    def kill_process_by_name(self,
                             pname: str,
                             sudo_required: bool = False,
                             multi_kill: bool = False):
        # collect pids
        # note: 'ignore' is necessary if nothing is found
        pids = self.client.exec(f'pgrep {pname}', ignore_rc=True).stdout.splitlines()

        # check status
        if len(pids) == 1 and multi_kill or len(pids) > 1 and not multi_kill:
            raise Exception(f'Something wrong: target host have few running {pname} processes but expected "{multi_kill}" multi killing')

        # killing
        if len(pids) > 0:
            pids_formatted = ' '.join(pids)
            cmd_string = f'kill -9 {pids_formatted}'
            if sudo_required:
                cmd_string = 'sudo ' + cmd_string
            self.client.exec(cmd_string)

        # close connection
        self.client.close()

    def exec_in_dedicated_session(self, cmd: str) -> SShResponse:
        resp = self.client.exec(cmd)
        self.client.close()
        return resp

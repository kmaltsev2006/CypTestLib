import allure
import pytest

from cyp_test_lib.helpers.string_check import check_elements_in_a_string
from cyp_test_lib.ssh_client import SshClient


@allure.suite('fio tests')
@pytest.mark.smoke
@pytest.mark.fio
class TestFio:

    @allure.title('fio: run test')
    def test_fio(self, ssh_client: SshClient):
        cmd = ssh_client.exec('fio --rw=read --direct=1 --bs=1M --ioengine=libaio --runtime=10 --numjobs=1 '
                              '--time_based --group_reporting --name=seq_read --iodepth=16 --size=128M')

        expected_items = ['Starting 1 process', 'Run status group 0 (all jobs):', 'Disk stats (read/write):']
        data = check_elements_in_a_string(cmd.stdout, expected_items)
        assert not data, f'fio can not correctly execute: following items {data} doesnt fit stdout [{cmd.stdout}]'

import allure
import pytest

from cyp_test_lib.helpers.string_check import check_elements_in_a_string


@allure.suite('htop tests')
@pytest.mark.smoke
@pytest.mark.htop
class TestHtop:

    @allure.title('htop test')
    def test_htop(self, ssh_client):
        # run htop and then send F10 functional key for exit, required TERM define
        cmd = ssh_client.exec('export TERM=xterm && tput kf21 | htop -u $(whoami) -M -C')

        expected_items = ['Tasks:', 'Load average:', 'Uptime:', 'Mem', 'Swp', 'Command', 'TIME+', 'CPU%-MEM%']
        data = check_elements_in_a_string(cmd.stdout, expected_items)
        assert not data, f'can not correctly run htop: following items {data} doesnt fit stdout [{cmd.stdout}]'

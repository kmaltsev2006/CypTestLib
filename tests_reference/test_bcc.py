import allure
import pytest

from cyp_test_lib.helpers.string_check import check_elements_in_a_string


@allure.suite('bcc tests')
@pytest.mark.smoke
@pytest.mark.bcc
class TestBcc:

    @allure.title('bcc: get bps')
    def test_bcc_bps(self, ssh_client):
        cmd = ssh_client.exec_sudo('bps')

        expected_items = ['BID TYPE', 'UID', '#MAPS', 'LoadTime', 'NAME']
        data = check_elements_in_a_string(cmd.stdout, expected_items)
        assert not data, ('bps can not correctly display existing disk partitions: '
                          f'following items {data} doesnt fit stdout [{cmd.stdout}]')

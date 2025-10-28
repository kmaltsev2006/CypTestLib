import allure
import pytest


@allure.suite('nano tests')
@pytest.mark.smoke
@pytest.mark.nano
class TestNano:

    @allure.title('nano: edit file')
    def test_nano_edit_file(self, ssh_client, temporary_file):
        phrase = 'Hello This World'
        ssh_client.exec(f'echo "{phrase}" > {temporary_file}')

        # test can not correctly save original file, but nano dump text to temporary buffer file
        added_phrase = ' <some skipped text>'
        cmd = ssh_client.exec(
            f'echo -e "^X" | echo -e "^S" | echo " {added_phrase} " | nano +1,7 {temporary_file}',
            ignore_rc=True)
        if 'nano: command not found' in cmd.stderr or 'Buffer written to ' not in cmd.stderr:
            pytest.fail(reason=f'Something wrong with nano, please check err msg: {cmd.stderr}')

        buffer_file = cmd.stderr.split()[-1]
        cmd = ssh_client.exec(f'cat {buffer_file}')

        expected_text = phrase[:5] + added_phrase + phrase[5:]
        assert expected_text == cmd.stdout, 'nano can not edit file'

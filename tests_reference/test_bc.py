import allure
import pytest


@allure.suite('bc tests')
@pytest.mark.smoke
@pytest.mark.bc
class TestBc:

    @allure.title('Bc: evaluate expression')
    def test_evaluate_bc(self, ssh_client):
        cmd = ssh_client.exec('echo "scale=4;10/3" | bc')
        assert '3.3333' == cmd.stdout, 'Bc package can not correctly evaluate expression'

    @allure.title('Dc: evaluate expression')
    def test_evaluate_dc(self, ssh_client, temporary_file):
        cmd = ssh_client.exec(f'echo -e "50\n10\n*\np\n" > {temporary_file} && dc -f {temporary_file}')
        assert '500' == cmd.stdout, 'Dc package can not correctly evaluate expression from file'

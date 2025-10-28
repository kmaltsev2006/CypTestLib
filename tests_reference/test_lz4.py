import os

import allure
import pytest

REL_FILE_PATH = 'test_files/'
DST_DIR = '/tmp/test/'
TMP_FILE = 'task_config.yaml'


@pytest.fixture(scope='function', autouse=True)
def wrapper(ssh_client):
    src = os.path.join(os.path.dirname(__file__), REL_FILE_PATH, TMP_FILE)
    ssh_client.exec(f'mkdir {DST_DIR}')
    ssh_client.put_file(src, DST_DIR)
    yield
    ssh_client.exec(f'rm -rf {DST_DIR}')


@allure.suite('lz4 tests')
@pytest.mark.smoke
@pytest.mark.lz4
class TestLz4:

    @allure.title('lz4: run lz4 compression')
    def test_lz4_compression(self, ssh_client):
        """
        Checking lz4 compression result
        """
        compr_file_name = 'test_compressed'
        ssh_client.exec(f'cd {DST_DIR}; lz4 {TMP_FILE} {compr_file_name}')
        ssh_client.exec(f'cd {DST_DIR}; ls | grep {compr_file_name}')
        data_compressed = ssh_client.exec(f'cd {DST_DIR}; ls -la {compr_file_name} | awk \'{{print $5}}\'')
        data_raw = ssh_client.exec(f'cd {DST_DIR}; ls -la {TMP_FILE} | awk \'{{print $5}}\'')
        assert data_compressed.stdout < data_raw.stdout, 'Compression did not work correctly'

    @allure.title('lz4: run lz4 decompression')
    def test_lz4_decompression(self, ssh_client):
        """
        Checking lz4 decompression result
        """
        compr_file_name = 'test_compressed'
        decompr_file_name = 'test_decompressed'
        ssh_client.exec(f'cd {DST_DIR}; lz4 {TMP_FILE} {compr_file_name}')
        ssh_client.exec(f'cd {DST_DIR}; lz4 -d {compr_file_name} {decompr_file_name}')
        ssh_client.exec(f'cd {DST_DIR}; ls | grep {decompr_file_name}')
        data_decompressed = ssh_client.exec(f'cd {DST_DIR}; ls -la {decompr_file_name} | awk \'{{print $5}}\'')
        data_raw = ssh_client.exec(f'cd {DST_DIR}; ls -la {TMP_FILE} | awk \'{{print $5}}\'')
        assert data_decompressed.stdout == data_raw.stdout, 'Decompression did not work correctly'

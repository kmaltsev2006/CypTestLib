import pytest

from tests.cyp_test_lib.helpers.remote_info import RemoteTargetInfo

r_client = RemoteTargetInfo()

virtual = r_client.is_virtual()
qemu = r_client.is_qemu()

skip_virtual = pytest.mark.skipif(virtual, reason='This test does not support virtual systems')
skip_qemu = pytest.mark.skipif(qemu, reason='This test does not support QEMU systems')
skip_dns = pytest.mark.skipif(not dns, reason='This test requires configured DNS')
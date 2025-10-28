import os

from tests.cyp_test_lib.ssh_client import SshClient

client = SshClient(
    host=os.getenv('TARGET'),
    port=os.getenv('TARGET_PORT'),
    user=os.getenv('TARGET_USER'),
    password=os.getenv('TARGET_PASSWORD'))


def check_services(services: list) -> bool:
    client.connect()
    services_found = True
    for service in services:
        data = client.exec(f'systemctl status {service}', ignore_rc=True)
        if data.rc != 0:
            services_found = False
    return services_found

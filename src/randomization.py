import random
import string


def rand_str(length: int = 4) -> str:
    """
    :param length: Length of random string
    :return: random string
    """
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=length))

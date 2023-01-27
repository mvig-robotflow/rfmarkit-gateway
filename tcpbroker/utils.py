import datetime
from typing import List

from IPy import IP


def parse_cidr_addresses(cidr: List[str]) -> List[str]:
    """
    Convert CIDR addresses to dotted decimal addresses
    :param cidr: CIDR address
    :return: address string

    Args:
        cidr: CIDR address

    Returns:
        list of address string
    """
    res = []
    for entry in cidr:
        res.extend([ip.strNormal() for ip in IP(entry)])
    return sorted(list(set(res)), key=lambda ip: IP(ip).int())


def get_datetime_tag() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

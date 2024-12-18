# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import getpass
import os
import platform
import subprocess
from enum import Enum
from sys import platform
from typing import List, Tuple


class OperatingSystem(Enum):
    LINUX = "LINUX"
    MAC = "MAC"
    WINDOWS = "WINDOWS"
    UNDEFINED = "UNDEFINED"


def get_os() -> "OperatingSystem":
    system = platform.system()
    if system == "Linux":
        return OperatingSystem.LINUX
    elif system == "Darwin":
        return OperatingSystem.MAC
    elif system == "Windows":
        return OperatingSystem.WINDOWS
    else:
        return OperatingSystem.UNDEFINED


def get_username() -> str:
    return getpass.getuser()


def get_cwd() -> str:
    return os.getcwd()


def get_available_clusters() -> List[Tuple[str, str, str]]:
    # TODO: Call with real clusters
    clusters = [
        ("192.0.2.141", "cluster-mm", "0.7.0"),
        ("192.0.2.142", "loke_b", "0.9.1"),
        ("192.0.2.143", "cluster-mm", "0.8.0"),
        ("192.0.2.72", "cluster-mm", "0.7.0"),
        ("0.0.0.0", "dummy", "0.0.0"),
    ]
    return clusters


def _parse_ss_redis_output(ss_in_: "subprocess.CompletedProcess") -> List[str]:
    redis_instances = set()
    for line in ss_in_.stdout.splitlines():
        if "redis-server" in line:
            parts = line.split()
            # Extract port
            address = parts[3]  # Local address including port

            # Parse the port from the local address
            port = address.split(":")[-1]
            redis_instances.add(port)

    return list(sorted(redis_instances))


def _get_available_redis_instances_linux() -> List[str]:
    try:
        # Get all running processes with `ps aux`
        ps_result = subprocess.run(
            ["ps", "aux"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Filter for Redis processes
        redis_pids = []
        for line in ps_result.stdout.splitlines():
            if "redis-server" in line:
                parts = line.split()
                pid = parts[1]  # PID is the second column in ps output
                redis_pids.append(pid)

        # For each Redis PID, check the listening ports
        redis_instances = set()
        for pid in redis_pids:
            # Run ss or netstat to get network connections for the PID
            net_result = subprocess.run(
                ["ss", "-ltnp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Parse the output and find connections for the Redis PID
            for line in net_result.stdout.splitlines():
                if pid in line:
                    parts = line.split()
                    address = parts[3]  # Local address (host:port)
                    port = address.split(":")[-1]  # Extract port from address
                    redis_instances.add(port)

        return list(sorted(redis_instances))

    except Exception as e:
        print("Error:", e)
        return []


def _get_available_redis_instances_wsl() -> List[str]:
    try:
        # Run `wsl ss` to list all listening TCP connections with process info
        result = subprocess.run(
            ["wsl", "ss", "-ltnp"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Parse the output to look for Redis instances
        return _parse_ss_redis_output(result)

    except Exception as e:
        print("Error:", e)
        return []


def _get_available_redis_instances_mac() -> List[str]:
    """
    Find all redis instances on macOS

    Returns: List of redis instances, sorted in ascending order

    """
    try:
        # Run `lsof` to list all processes with network connections
        result = subprocess.run(
            ["lsof", "-iTCP", "-sTCP:LISTEN"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Parse the output to find Redis instances
        redis_instances = set()
        for line in result.stdout.splitlines():
            if "redis-ser" in line:
                parts = line.split()
                port_info = parts[8]

                # Extract the port from the port information (e.g., "*:6379" or "localhost:6380")
                port = port_info.split(":")[-1]
                redis_instances.add(port)
        return list(sorted(redis_instances))

    except Exception as e:
        print("Error:", e)
        return []


def get_available_redis_instances() -> List[str]:
    """
    This is a robust implementation to find a redis instance cross-platform

    Returns: List of redis instances, sorted in ascending order

    """
    operating_system_ = get_os()
    if operating_system_ == OperatingSystem.LINUX:
        return _get_available_redis_instances_linux()
    elif operating_system_ == OperatingSystem.MAC:
        return _get_available_redis_instances_mac()
    elif operating_system_ == OperatingSystem.WINDOWS:
        return _get_available_redis_instances_wsl()
    else:
        return []


def get_cluster_modules() -> List[Tuple[str, str]]:
    modules = [
        ("module0", "QCM"),
        ("module1", "QCM"),
        ("module2", "QCM"),
        ("module3", "QCM"),
        ("module4", "QCM"),
        ("module5", "QCM"),
        ("module6", "QRM"),
        ("module7", "QRM"),
    ]
    return modules


if __name__ == "__main__":
    print(get_available_redis_instances())

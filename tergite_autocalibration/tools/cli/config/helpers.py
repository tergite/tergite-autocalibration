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

import os
from typing import List, Tuple


def get_username() -> str:
    return os.getlogin()


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


def get_available_redis_instances() -> List[str]:
    # TODO: Find a way to grep the redis instances efficiently via some low level functions
    redis_instances = ["6379", "6380"]
    return redis_instances


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

# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs AB 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


import json

import fakeredis
import pytest

from tergite_autocalibration.utils.backend.redis_backup import (
    dump_redis_to_json,
    load_json_to_redis,
)


@pytest.fixture
def redis_session():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def test_file(tmp_path):
    return tmp_path / "test_dump.json"


def test_dump_redis_to_json(redis_session, test_file):
    """
    Go through basic cases of dumping data.
    """

    # Setup test data in Redis
    redis_session.set("string_key", "string_value")
    redis_session.lpush("list_key", "item1", "item2")
    redis_session.sadd("set_key", "member1", "member2")
    redis_session.hset("hash_key", "field1", "value1")
    redis_session.zadd("zset_key", {"member1": 1.0, "member2": 2.0})

    # Call the function
    dump_redis_to_json(redis_session, test_file)

    # Read the output file
    with open(test_file, "r") as f:
        data = json.load(f)

    # Assertions
    assert data["string_key"]["type"] == "string"
    assert data["string_key"]["value"] == "string_value"
    assert data["list_key"]["type"] == "list"
    assert data["list_key"]["value"] == ["item2", "item1"]
    assert data["set_key"]["type"] == "set"
    # Sets are serialized as lists
    assert set(data["set_key"]["value"]) == {"member1", "member2"}
    assert data["hash_key"]["type"] == "hash"
    assert data["hash_key"]["value"] == {"field1": "value1"}
    assert data["zset_key"]["type"] == "zset"
    # Scores are serialized as strings and parsed as floats while loading
    assert data["zset_key"]["value"] == {"member1": "1.0", "member2": "2.0"}


def test_load_json_to_redis(redis_session, test_file):
    """
    Go through basic cases of loading data
    """

    # Setup test JSON data
    test_data = {
        "string_key": {"type": "string", "value": "string_value"},
        "list_key": {"type": "list", "value": ["item1", "item2"]},
        "set_key": {"type": "set", "value": ["member1", "member2"]},
        "hash_key": {"type": "hash", "value": {"field1": "value1"}},
        "zset_key": {"type": "zset", "value": {"member1": 1.0, "member2": 2.0}},
    }

    # Write test data to file
    with open(test_file, "w") as f_:
        json.dump(test_data, f_)

    # Call the function
    load_json_to_redis(test_file, redis_session)

    # Assertions
    assert redis_session.get("string_key") == "string_value"
    assert redis_session.lrange("list_key", 0, -1) == ["item1", "item2"]
    assert redis_session.smembers("set_key") == {"member1", "member2"}
    assert redis_session.hgetall("hash_key") == {"field1": "value1"}
    assert redis_session.zrange("zset_key", 0, -1, withscores=True) == [
        ("member1", 1.0),
        ("member2", 2.0),
    ]


def test_dump_load_redis(redis_session, test_file):
    """
    Combine the two functions above
    """

    # Setup test data in Redis
    redis_session.set("string_key", "string_value")
    redis_session.lpush("list_key", "item1", "item2")
    redis_session.sadd("set_key", "member1", "member2")
    redis_session.hset("hash_key", "field1", "value1")
    redis_session.zadd("zset_key", {"member1": 1.0, "member2": 2.0})

    # Call the function
    dump_redis_to_json(redis_session, test_file)

    redis_session.flushall()

    # Call the function
    load_json_to_redis(test_file, redis_session)

    # Assertions
    assert redis_session.get("string_key") == "string_value"
    assert redis_session.lrange("list_key", 0, -1) == ["item2", "item1"]
    assert redis_session.smembers("set_key") == {"member1", "member2"}
    assert redis_session.hgetall("hash_key") == {"field1": "value1"}
    assert redis_session.zrange("zset_key", 0, -1, withscores=True) == [
        ("member1", 1.0),
        ("member2", 2.0),
    ]

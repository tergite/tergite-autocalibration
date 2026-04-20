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
from pathlib import Path
from typing import TYPE_CHECKING, Union, Dict, Any

if TYPE_CHECKING:
    import redis


def dump_redis(redis_session: "redis.Redis") -> Dict[str, Any]:
    """
    Dump all values for a redis database into a json file.

    Output should look similar to:
    ```
    "device:qubit:07:pi_pulse_ef_amplitude:unit": {
        "type": "string",
        "value": "'V'"
    },
    "transmons:q07": {
        "type": "hash",
        "value": {
            "t1_time": "nan",
            "spec:spec_duration": "6e-06",
            "spec:spec_ampl_12_optimal": "0.03",
            ...
        }
    }
    ```

    Args:
        redis_session: Session used to access the redis database. Assumes decode_responses=True.

    """
    data = {}

    # Iterate over all keys
    for key in redis_session.scan_iter():
        key_type = redis_session.type(key)

        if key_type == "string":
            data[key] = {
                "type": "string",
                "value": redis_session.get(key),
            }
        elif key_type == "list":
            data[key] = {
                "type": "list",
                "value": [item for item in redis_session.lrange(key, 0, -1)],
            }
        elif key_type == "set":
            data[key] = {
                "type": "set",
                "value": list(redis_session.smembers(key)),
            }
        elif key_type == "hash":
            hash_data = {}
            for field, value in redis_session.hgetall(key).items():
                hash_data[field] = value
            data[key] = {"type": "hash", "value": hash_data}
        elif key_type == "zset":
            zset_data = {}
            for member, score in redis_session.zrange(key, 0, -1, withscores=True):
                zset_data[member] = str(score)
            data[key] = {"type": "zset", "value": zset_data}

    return data


def dump_redis_to_json(redis_session: "redis.Redis", output_file: Union[Path, str]):
    """
    Wraps dump_redis and saves output to a json file.

    Args:
        redis_session: Redis session to take data from.
        output_file: JSON file to write to.
    """
    data = dump_redis(redis_session)

    # Save to json file
    with open(output_file, "w", encoding="utf-8") as f_:
        json.dump(data, f_, indent=2)


def load_redis(input_values: Dict[str, Any], redis_session: "redis.Redis") -> None:
    """
    Load json formatted redis values into a redis database.

    Input data should look similar to:
    ```
    "device:qubit:07:pi_pulse_ef_amplitude:unit": {
        "type": "string",
        "value": "'V'"
    },
    "transmons:q07": {
        "type": "hash",
        "value": {
            "t1_time": "nan",
            "spec:spec_duration": "6e-06",
            "spec:spec_ampl_12_optimal": "0.03",
            ...
        }
    }
    ```

    Args:
        input_values: Values to load to redis as dict.
        redis_session: Redis session to take data from.

    """
    # Iterate over json contents
    for key, value in input_values.items():
        if value["type"] == "string":
            redis_session.set(key, value["value"])
        elif value["type"] == "list":
            for item in value["value"]:
                redis_session.rpush(key, item)
        elif value["type"] == "set":
            for item in value["value"]:
                redis_session.sadd(key, item)
        elif value["type"] == "hash":
            for field, field_value in value["value"].items():
                redis_session.hset(key, field, field_value)
        elif value["type"] == "zset":
            for member, score in value["value"].items():
                redis_session.zadd(key, {member: float(score)})


def load_json_to_redis(
    input_file: Union[Path, str], redis_session: "redis.Redis"
) -> None:
    """
    Load json formatted redis values into a redis database.

    Args:
        input_file: Input file with data dumped.
        redis_session: Redis session used to access the redis database. Assumes decode_responses=True.

    """
    with open(input_file, "r") as f:
        data = json.load(f)

    load_redis(data, redis_session)

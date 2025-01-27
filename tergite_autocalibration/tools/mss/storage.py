# This code is part of Tergite
#
# (C) Copyright David Wahlstedt 2023
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import ast
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique
from numbers import Number
from typing import Any, List, Tuple, TypeVar
from typing import Hashable, Optional

import redis

import tergite_autocalibration.config.globals
from tergite_autocalibration.utils.logging import logger


def to_string(o: object) -> Optional[str]:
    """Converts its argument into a string, such that
    ast.literal_eval(o) == o.  The reason for not just using repr for
    this purpose is that repr might be overridden by debugging tools,
    or hypothetically, repr could change between python versions.

    NOTE: the might be objects that we haven't covered yet: they can
    be added later.
    """

    if isinstance(o, Number):
        return str(o)
    elif o is None:
        return str(o)
    elif isinstance(o, str):
        # quote the string
        return f"'{o}'"
    if isinstance(o, bytes):
        return str(o)
    elif isinstance(o, list):
        parts = [to_string(e) for e in o]
        return f"[{', '.join(parts)}]"
    elif isinstance(o, tuple):
        parts = [to_string(e) for e in o]
        return f"({', '.join(parts)})"
    elif isinstance(o, dict):
        parts = [f"{_quote_key(key)}: {to_string(value)}" for key, value in o.items()]
        return f"{{{', '.join(parts)}}}"
    else:
        logger.error(f"Unsupported object: {o}")
        logger.error("(was the calling function)", stacklevel=2)
        return None


def _quote_key(key: Hashable) -> Hashable:
    """Quotes a dict key if it is a string, and otherwise just returns it"""
    if isinstance(key, str):
        return f"'{key}'"
    else:
        return key


"""Read and write ISO 8601 UTC Z timestamps

Since Python's standard libraries don't support the Z suffix, we
provide these helper functions.
"""


def utc_now_iso(precision=6) -> str:
    """Returns current time as an ISO 8601 UTC Z string.

    If precision=n is provided, the fractional part of the seconds is
    truncated to n decimals.
    """
    s = datetime.utcnow()
    return utc_to_iso(s, precision)


def utc_to_iso(t: datetime, precision=6) -> str:
    """Converts a datetime instance in UTC into an ISO 8601 UTC Z string.

    If precision=n is provided, the fractional part of the seconds is
    truncated to n decimals.

    NOTES: The given time t *MUST* be in UTC. If the timestamp was
    created by utcfromtimestamp, this function is suitable.
    """
    s = t.isoformat()
    if precision == 0:
        s = s[:-7]  # remove microseconds and trailing decimal point
    elif precision in range(1, 6):  # [1..5]
        s = s[: -(6 - precision)]  # note that s[:-0] == ""
    elif precision != 6:
        logger.info(f"invalid precision {precision}: defaulting to 6 (microseconds)")

    return s + "Z"


# ============================================================================
# Types
# ============================================================================

Unit = str

TimeStamp = str  # in ISO 8601 UTC Z with microsecond precision

# Types for some measurement data

Frequency = float
Voltage = float

Hex = str  # type(hex(5))

# ============================================================================
# Initialization for Redis storage
# ============================================================================

red = tergite_autocalibration.config.globals.REDIS_CONNECTION

# ============================================================================
# Constants
# ============================================================================

TRANSACTION_MAX_RETRIES = 100

# =============================================================================
# Class definitions for storage data model
# =============================================================================

Counter = int

T = TypeVar("T")

# Since a class name is not allowed as type hint in its method
# declarations (see PEP 563), we introduce the following, for use in
# type hints:
_BackendProperty = Any


@unique
class PropertyType(str, Enum):
    DEVICE = "device"  # the string returned by str
    ENVIRONMENT = "environment"
    SETUP = "setup"

    def __str__(self) -> str:
        return str.__str__(self)


@dataclass
class BackendProperty:
    property_type: PropertyType

    name: str  # property name e.g. resonant_frequency
    value: Optional[T] = None  # the value of the property
    unit: Optional[Unit] = None

    component: Optional[str] = None  # "resonator", "qubit", "coupler"
    component_id: Optional[str] = (
        None  # component id, e.g. "1", "2", etc, or perhaps "q1", "q2", etc
    )

    long_name: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None  # "measurement", "config", or "mock_up"

    def write_value(self) -> bool:
        """Write the "value" field to Redis. Set the timestamp, and
        increase the counter. Return True if write succeeded, and
        False otherwise.
        """

        # Question: should we require that metadata is set before
        # allowing access to the value?

        value_key = self._create_redis_key("value")
        count_key = self._create_redis_key("count")
        timestamp_key = self._create_redis_key("timestamp")
        watch_keys = [value_key, count_key, timestamp_key]

        def set_fields(pipe):
            pipe.set(value_key, to_string(self.value))
            pipe.set(timestamp_key, to_string(utc_now_iso()))
            pipe.incrby(count_key, 1)

        results = _transaction(watch_keys, set_fields)
        return results is not None

    def write_metadata(self) -> bool:
        """Write all non-None fields to Redis except for the "value"
        field. Set the timestamp, but don't increase the counter.
        """
        metadata = [
            (field, value)
            for field, value in self.__dict__.items()
            if field in _included_fields - set(["value"]) and value is not None
        ]
        timestamp_key = self._create_redis_key("timestamp")

        def set_fields(pipe):
            for field, value in metadata:
                field_key = self._create_redis_key(field)
                pipe.set(field_key, to_string(value))
            pipe.set(timestamp_key, to_string(utc_now_iso()))

        results = _transaction([timestamp_key], set_fields)
        return results is not None

    def write(self) -> bool:
        """Write the whole record into Redis. Suitable for initialization."""
        success = self.write_metadata()
        success = success and self.write_value()
        return success

    @classmethod
    def read(
        cls,
        property_type: PropertyType,
        name: str,
        component: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> Optional[Tuple[_BackendProperty, TimeStamp, Counter]]:
        """Get the backend property from Redis associated with kind,
        name, component, and component_id, when relevant, together with its
        metadata fields, plus Counter and TimeStamp (that are not
        class members)
        """

        value_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="value",
        )
        count_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="count",
        )
        timestamp_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="timestamp",
        )
        watch_keys = [value_key, count_key, timestamp_key]
        fields = list(_included_fields)

        def get_fields(pipe):
            for field in fields:
                field_key = create_redis_key(
                    property_type,
                    name,
                    component=component,
                    component_id=component_id,
                    field=field,
                )
                pipe.get(field_key)
            # these two are not class members:
            pipe.get(timestamp_key)
            pipe.get(count_key)

        results = _transaction(watch_keys, get_fields)
        if results is None:
            return

        field_entries = dict(
            {
                # all values v were created with to_string(v), therefore
                # ast.literal_eval is safe here, unless something else has
                # gone seriously wrong
                (field, ast.literal_eval(value))
                for field, value in zip(fields + ["timestamp", "count"], results)
                if value is not None  # don't include keys absent in Redis
            }
        )
        # as long as field_entries is non-empty, we can instantiate
        if field_entries:
            # isolate the non-class member fields
            timestamp = field_entries.pop("timestamp", None)
            count = field_entries.pop("count", None)
            return (
                cls(
                    property_type=property_type,
                    name=name,
                    component=component,
                    component_id=component_id,
                    **field_entries,
                ),
                timestamp,
                count,
            )
        else:
            # None of the fields had any Redis entry stored
            return

    @classmethod
    def read_value(
        cls,
        property_type: PropertyType,
        name: str,
        component: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> Optional[T]:
        """Return the value associated with kind, name, component and
        component_id (if relevant).
        Note: we don't use transactions here, but maybe we should?
        """
        value_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="value",
        )
        result = red.get(value_key)
        return (
            ast.literal_eval(result)
            if result is not None and str(result).lower() != "nan"
            else None
        )

    def _create_redis_key(self, field: Optional[str] = None) -> str:
        return create_redis_key(
            self.property_type,
            self.name,
            component=self.component,
            component_id=self.component_id,
            field=field,
        )

    @classmethod
    def get_counter(
        cls,
        property_type: PropertyType,
        name: str,
        component: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> Optional[int]:
        # Gets the counter value of the property associated to the
        # given fields. If no counter value is set yet, but there is
        # metadata written, 0 is returned as counter value.
        #
        # Note: the counter value represents how many times the value
        # has been updated.
        #
        # Question: should we have this in a transaction?
        key_stem = create_redis_key(
            property_type, name, component=component, component_id=component_id
        )
        if next(red.scan_iter(key_stem + "*"), None) is None:
            return None

        count_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="count",
        )
        result = red.get(count_key)
        # if the metadata is set, but the counter is not yet
        # incremented, treat it as 0
        return int(result) if result is not None else 0

    @classmethod
    def reset_counter(
        cls,
        property_type: PropertyType,
        name: str,
        component: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> bool:
        """Reset the associated counter. Return True if successful,
        and False otherwise.
        """
        value_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="value",
        )
        count_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="count",
        )
        # should we set a new timestamp when the counter is reset?
        timestamp_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="timestamp",
        )
        watch_keys = [value_key, count_key, timestamp_key]

        def set_fields(pipe):
            pipe.set(count_key, 0)
            pipe.set(timestamp_key, to_string(utc_now_iso()))

        results = _transaction(watch_keys, set_fields)
        return results is not None

    @classmethod
    def get_timestamp(
        cls,
        property_type: PropertyType,
        name: str,
        component: Optional[str] = None,
        component_id: Optional[str] = None,
    ) -> Optional[int]:
        """Returns the timestamp of the property associated with kind,
        name, component, and component_id. If no property is associated,
        return None.
        """
        timestamp_key = create_redis_key(
            property_type,
            name,
            component=component,
            component_id=component_id,
            field="timestamp",
        )
        result = red.get(timestamp_key)
        # The timestamp was stored by to_string as a quoted string, and
        # will now be turned into an unquoted string
        return (
            ast.literal_eval(result)
            if result is not None and str(result).lower() != "nan"
            else None
        )

    @classmethod
    def delete_property(
        cls,
        property_type: PropertyType,
        name: str,
        component: Optional[str] = None,
        component_id: Optional[str] = None,
    ):
        """Deletes all Redis the key-value bindings associated with
        the identified property.
        """
        key_stem = create_redis_key(
            property_type, name, component=component, component_id=component_id
        )
        for key in red.scan_iter(key_stem + "*"):
            red.delete(key)


# The fields of BackendProperty as a set
_all_fields = set(BackendProperty.__dataclass_fields__.keys())

# These fields are part of the key (when present), so they don't need
# to be stored as fields in Redis
_excluded_fields = set(["property_type", "name", "component", "component_id"])

# Only these are stored in Redis, the others are part of the key
_included_fields = _all_fields - _excluded_fields


# =============================================================================
# Local helper functions
# =============================================================================


def _transaction(watch_keys: List[str], command: callable) -> Optional[list]:
    """Perform 'command', watching 'watch_keys'. If any of the watch
    keys are modified in Redis during execution of 'command', the
    command will be discarded and re-attempted, at most
    TRANSACTION_MAX_RETRIES times. If it doesn't succeed then, None is
    returned. If successful, a list of results of the pipeline
    operation results is returned.
    """
    with red.pipeline() as pipe:
        n_retries = 0
        while True:
            try:
                pipe.watch(*watch_keys)
                pipe.multi()
                command(pipe)  # this does what should be inside the transaction
                results = pipe.execute()
                return results
            except redis.WatchError as e:
                n_retries += 1
                logger.warning(
                    f"{e}, at least one of {' ,'.join(watch_keys)} were changed by "
                    f"another process: retrying, {n_retries=}"
                )
                logger.warning("(caller location)", stacklevel=2)
                if n_retries > TRANSACTION_MAX_RETRIES:
                    logger.warning(
                        f"Transaction failed, since max number of allowed "
                        f"retries ({TRANSACTION_MAX_RETRIES}) were exceeded."
                    )
                    return


# =============================================================================
# Public helper functions
# =============================================================================


def create_redis_key(
    property_type: PropertyType,
    name: str,
    component: Optional[str] = None,
    component_id: Optional[str] = None,
    field: Optional[str] = None,
) -> str:
    """Creates a Redis key from the given arguments, identifying a
    backend property. If 'field' is omitted, the key obtained is a
    common prefix for all keys associated with the property.

    Note: made public in order to allow other functions(e.g. in
    calibration framework) to use keys that may contain this key,
    without relying on how it actually looks.
    """
    opt_component = f":{component}" if component else ""
    opt_component_id = f":{component_id}" if component_id != None else ""
    opt_field = f":{field}" if field else ""
    # f"{property_type}" == str(property_type), so we get the right string value
    return f"{property_type}{opt_component}{opt_component_id}:{name}{opt_field}"


"""Component helpers"""


def set_component_property(
    component: str,
    name: str,
    component_id: str,
    **fields,
):
    """Set the component device property identified by
    property_type, name, component, and component_id, to the bindings given
    in fields.
    """
    property_type = PropertyType.DEVICE
    p = BackendProperty(
        property_type, name, component=component, component_id=component_id, **fields
    )
    p.write_metadata()
    p.write_value()


def get_component_property(
    component: str,
    name: str,
    component_id: str,
) -> Optional[Tuple[_BackendProperty, TimeStamp, Counter]]:
    property_type = PropertyType.DEVICE
    return BackendProperty.read(
        property_type, name, component=component, component_id=component_id
    )


def get_component_value(
    component: str,
    name: str,
    component_id: str,
) -> Optional[T]:
    property_type = PropertyType.DEVICE
    return BackendProperty.read_value(
        property_type, name, component=component, component_id=component_id
    )


"""Resonator helpers"""


def set_resonator_property(name: str, component_id: str, **fields):
    """Write given fields into Redis for resonator property identified
    by the given arguments.
    """
    set_component_property("resonator", name, component_id, **fields)


def get_resonator_property(
    name: str, component_id: str
) -> Optional[Tuple[_BackendProperty, TimeStamp, Counter]]:
    """Get all fields associated with the resonator property
    identified by the given arguments.
    """
    return get_component_property("resonator", name, component_id)


def set_resonator_value(name: str, component_id: str, value: T):
    """Write given value into Redis for resonator property identified
    by the given arguments.
    """
    set_component_property("resonator", name, component_id, value=value)


def get_resonator_value(name: str, component_id: str) -> Optional[T]:
    """Get the value associated with the resonator property
    identified by the given arguments.
    """
    return get_component_value("resonator", name, component_id)


"""Qubit helpers"""


def set_qubit_property(name: str, component_id: str, **fields):
    """Write given fields into Redis for qubit property identified
    by the given arguments.
    """
    set_component_property("qubit", name, component_id, **fields)


def get_qubit_property(
    name: str, component_id: str
) -> Optional[Tuple[_BackendProperty, TimeStamp, Counter]]:
    """Get all fields associated with the qubit property
    identified by the given arguments.
    """
    return get_component_property("qubit", name, component_id)


def set_qubit_value(name: str, component_id: str, value: T):
    """Write given value into Redis for qubit property identified
    by the given arguments.
    """
    set_component_property("qubit", name, component_id, value=value)


def get_qubit_value(name: str, component_id: str) -> Optional[T]:
    """Get the value associated with the qubit property
    identified by the given arguments.
    """
    return get_component_value("qubit", name, component_id)


"""Coupler helpers"""


def set_coupler_property(name: str, component_id: str, **fields):
    """Write given fields into Redis for coupler property identified
    by the given arguments.
    """
    set_component_property("coupler", name, component_id, **fields)


def get_coupler_property(
    name: str, component_id: str
) -> Optional[Tuple[_BackendProperty, TimeStamp, Counter]]:
    """Get all fields associated with the coupler property
    identified by the given arguments.
    """
    return get_component_property("coupler", name, component_id)


def set_coupler_value(name: str, component_id: str, value: T):
    """Write given value into Redis for coupler property identified
    by the given arguments.
    """
    set_component_property("coupler", name, component_id, value=value)


def get_coupler_value(name: str, component_id: str) -> Optional[T]:
    """Get the value associated with the coupler property
    identified by the given arguments.
    """
    return get_component_value("coupler", name, component_id)

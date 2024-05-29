# This code is part of Tergite
#
# (C) Copyright David Wahlstedt 2022
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from datetime import datetime

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
    created by utcfromtimestamp, this function is suitalbe.
    """
    s = t.isoformat()
    if precision == 0:
        s = s[:-7]  # remove microseconds and trailing decimal point
    elif precision in range(1, 6):  # [1..5]
        s = s[: -(6 - precision)]  # note that s[:-0] == ""
    elif precision != 6:
        print(f"invalid precision {precision}: defaulting to 6 (microsecods)")

    return s + "Z"

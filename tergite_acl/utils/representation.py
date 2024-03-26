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

from numbers import Number
from typing import Hashable, Optional

from .logger.bcc_logger import get_logger

logger = get_logger()


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

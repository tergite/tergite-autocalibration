# This code is part of Tergite
#
# (C) Copyright Joel Sandås 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


def exponential_decay_function(m: float, p: float, amplitude: float, offset: float) -> float:
    """
    Exponential decay function.
    :param m: Exponent base.
    :param p: Decay factor.
    :param amplitude: Amplitude.
    :param offset: Offset.
    :return: Result of the exponential decay function.
    """
    return amplitude * p ** m + offset

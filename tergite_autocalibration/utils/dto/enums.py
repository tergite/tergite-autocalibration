# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023
# (C) Copyright Stefan Hill 2024
# (C) Copyright Michele Faucci Giannelli 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from enum import Enum


class DataStatus(Enum):
    """
    Used by check_data to indicate outcome
    """

    in_spec = 1
    out_of_spec = 2
    bad_data = 3
    undefined = 4


class CalibrationResultStatus(Enum):
    """
    Used by check_data to indicate outcome
    """

    success = 1
    failed = 2


class SamplespaceStructure(Enum):
    """
    In most of the measurements, the settable quantities can be considered 'orthogonal'
    in the sense that all settable point combinations correspond to a particular measurement.
    For example in a typical spectroscopy you sweep frequencies and amplitudes. Every measurement
    M corresponds to a distinct (freq, ampl) pair:
    ```
    amplitudes
    ^
    |
    |
    |     * M(fr,amp)
    |
    |
    |
    |-------------------> frequencies
    ```

    In all the schedules this manifests as nested for loops:
    ```
    for value_1 in settable_values_1:
        for value_2 in settable_values_2:
             do stuff
             Measure()
    ```

    However, in some particular nodes such as the `coupler_dc_spectroscopy` you cannot describe the samplespace
    as 'orthogonal' at least not in a clean way.The main reason is that this consists of two disconnected measurements
    one after the other. The samplespace looks 'parallel':

    ```
         * M(qub_f)                                    * M(ro_f)
    -------------------> qub_frequencies and then -------------------> ro_frequencies
    ```

    In the schedule this manifests as two decoupled for loops:

    ```
    for value_1 in settable_values_1:
        do stuff
        Measure()
    for value_2 in settable_values_2:
        do other stuff
        Measure()
    ```
    """

    ORTHOGONAL = "ORTHOGONAL"
    PARALLEL = "PARALLEL"


class MeasurementMode(Enum):
    """
    Used to set the cluster mode e.g.  real cluster or re analyse
    """

    real = 0
    dummy = 1
    re_analyse = 2


class ApplicationStatus(Enum):
    """
    Used to check in which state the application is as a whole.
    """

    # The application is just started and running.
    # This is the usual case in the beginning.
    ACTIVE = "ACTIVE"

    # The calibration has finished without software errors.
    # There could be still errors in some analysis functions.
    SUCCESS = "SUCCESS"

    # Some kind of error occurred, the application has stopped.
    FAILED = "FAILED"


class QubitRole(Enum):
    """
    Defines whether a qubit is target or control for a given coupler
    """

    TARGET = "TARGET"
    CONTROL = "CONTROL"
    NOTSET = "NOTSET"

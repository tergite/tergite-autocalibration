# This code is part of Tergite
#
# (C) Copyright Liangyu Chen 2023
# (C) Copyright Martin Ahindura 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import typing

from tergite_autocalibration.utils.QPU_connections_visualization import QPU, QPU_element
from tergite_autocalibration.utils.logging import logger


# TODO: TO Liangyu


def create_coupler_marking(qpu: typing.List[QPU_element]):
    edge_dict = {}

    # iterate over qubits
    for q1 in qpu:
        q1: "QPU_element"
        x1, y1 = q1.grid_coords
        for q2 in qpu:
            q2: "QPU_element"
            x2, y2 = q2.grid_coords

            # skip if it is the same qubit
            if q1.label == q2.label:
                continue

            if q1.label < q2.label:
                identifier = f"{q1.label}_{q2.label}"
            else:
                identifier = f"{q2.label}_{q1.label}"

            # skip if the coupler is already marked
            if identifier in edge_dict:
                continue

            # 1 + 2: same row
            if y1 == y2 and (x2 - x1) == 1:
                # 1: first qubit x even
                if x1 + y1 % 2 == 0:
                    edge_dict[identifier] = 1
                # 2: first qubit x uneven
                if x1 + y1 % 2 == 1:
                    edge_dict[identifier] = 2

            # 3 + 4: same col
            if x1 == x2 and (y2 - y1) == 1:
                # 3: first qubit y even
                if x1 + y1 % 2 == 0:
                    edge_dict[identifier] = 3
                # 2: first qubit y uneven
                if x1 + y1 % 2 == 1:
                    edge_dict[identifier] = 4

    return edge_dict


if __name__ == "__main__":
    coupler_marking = create_coupler_marking(QPU)
    logger.info(coupler_marking)

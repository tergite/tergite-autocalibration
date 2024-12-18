# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2023, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from tergite_autocalibration.utils.logger import logger


def draw_arrow_chart(header: str, node_list: list[str]):
    """
    Draw the chart of the node sequence on the command line

    Args:
        header: Headline description
        node_list: Node sequence to print

    Returns:

    """
    total_length = sum([6 for _ in node_list]) + max(
        list(map(lambda x_: len(x_), node_list))
    )
    total_length = max(60, total_length)
    logger.status("\u2554" + "\u2550" * total_length + "\u2557")
    length = 0
    logger.status(
        "\u2551" + " " + header + " " * (total_length - len(header) - 1) + "\u2551"
    )
    for i, item in enumerate(node_list):
        if i < len(node_list):
            logger.status(
                "\u2551"
                + " " * length
                + "\u21aa"
                + " "
                + item
                + " " * (total_length - length - len(item) - 2)
                + "\u2551"
            )
            length += 6
    logger.status("\u255a" + "\u2550" * total_length + "\u255d")

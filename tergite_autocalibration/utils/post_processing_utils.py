# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import matplotlib.pyplot as plt
import numpy as np
import xarray


def manage_plots(
    result_dataset: xarray.Dataset, column_grid: int, plots_per_qubit: int
):
    n_vars = len(result_dataset.data_vars)
    n_coords = len(result_dataset.coords)

    rows = int(np.ceil(n_vars / column_grid))
    rows = rows * plots_per_qubit

    fig, axs = plt.subplots(
        nrows=rows,
        ncols=np.min((n_vars, n_coords, column_grid)),
        squeeze=False,
        figsize=(column_grid * 5, rows * 5),
    )

    return fig, axs

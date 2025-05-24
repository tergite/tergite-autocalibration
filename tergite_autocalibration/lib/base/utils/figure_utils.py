# This code is part of Tergite
#
# (C) Copyright Michele Faucci Giannelli 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from pathlib import Path
from datetime import datetime
from matplotlib import gridspec
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from tergite_autocalibration.config.globals import (
    CONFIG,
)
from tergite_autocalibration.utils.logging import logger


def _add_top_band(
    axes_tuple,
):

    ax_left, ax_center, ax_right = axes_tuple

    # Shared background color
    for ax in axes_tuple:
        ax.set_facecolor("#f0f0f0")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")  # turns off everything: ticks, labels, spines

    # Divider line
    line = Line2D(
        [0.01, 0.99],
        [0, 0],
        color="black",
        linewidth=1,
        transform=ax_center.transAxes,
        zorder=10,
    )
    ax_center.add_line(line)

    # Add left logo, this is hardcoded as it is the Tergite logo.
    logo_path = ("resources/logo.png",)

    if logo_path:
        try:
            logo = mpimg.imread(logo_path)
            ax_left.imshow(logo, extent=[0, 1, 0, 1], aspect="auto")
        except Exception as e:
            logger.error(f"Left logo load failed: {e}")

    # Center text block
    acquisition_date = _infer_date_from_path(CONFIG.run.data_dir)
    analysis_date = datetime.now().strftime("%d-%m-%Y")

    if acquisition_date is None:
        acquisition_date = "Unknown"

    date_info = f"Acquisition: {acquisition_date}"
    if analysis_date:
        date_info += f" | Analysis: {analysis_date}"

    # Add text info (fill the rest of the band)
    # Chip information should be loaded from the device
    # config file, like the run info is taken from the run config,
    # but for now we hardcode it as CONFIG does not load the object correctly
    chip_name = "25-Qubit V8a #1"  # CONFIG.device.name
    chip_owner = "QC2"  # CONFIG.device.owner
    cooldown = CONFIG.run.cooldown
    right_logo_path = CONFIG.run.runner_logo

    label = None
    if CONFIG.run.is_internal:
        label = "Internal"

    full_text = f"{chip_owner} {chip_name} | CL: {cooldown} | {date_info}"
    if label is not None:
        full_text += f" | {label}"

    ax_center.text(
        0.02,
        0.5,
        full_text,
        va="center",
        ha="left",
        fontsize=14,
        weight="bold",
        transform=ax_center.transAxes,
        zorder=10,
    )

    if right_logo_path:
        try:
            logo = mpimg.imread(right_logo_path)
            width = 0.8
            ax_right.imshow(
                logo, extent=[0.1, 0.1 + width * 0.8, 0.1, 0.9], aspect="auto"
            )
        except Exception as e:
            logger.error(f"Right logo load failed: {e}")


def _infer_date_from_path(path: str) -> str:
    try:
        path = Path(path)
        # Try multiple formats in case of different naming conventions
        for part in path.parts:
            try:
                return datetime.strptime(part, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                pass

            # If no format matches, return folder creation time as fallback
        return datetime.fromtimestamp(path.stat().st_ctime).strftime("%d-%m-%Y")
    except Exception:
        return "Unknown"


def create_figure_with_top_band(nrows, ncols) -> tuple:
    """
    Create a figure with a top band for metadata and a grid of subplots.
    Args:
        nrows (int): Number of rows in the subplot grid.
        ncols (int): Number of columns in the subplot grid.
    Returns:
        fig (matplotlib.figure.Figure): The created figure.
        axs (numpy.ndarray): 2D array of Axes objects for the subplots.
    """
    # These values are fixed to ensure uniformity in the plots across the application.
    subplot_size = 5
    logo_size = 0.8
    band_height_inch = 0.8
    # This will fine tune the figure size based on the number of columns so that the writing no top fits
    if ncols == 1:
        subplot_size = 16
    elif ncols == 2:
        subplot_size = 8
    elif ncols == 3:
        subplot_size = 5.5

    fig_width = ncols * subplot_size
    subplot_area_height = nrows * subplot_size
    fig_height = band_height_inch + subplot_area_height

    fig = plt.figure(figsize=(fig_width, fig_height))

    # Outer GridSpec: 1 row for top band + 1 row for the subplot area
    outer = gridspec.GridSpec(
        2, 1, height_ratios=[band_height_inch, subplot_area_height], figure=fig
    )

    # Subplots (nrows x ncols) — this is the only one with spacing!
    plot_gs = gridspec.GridSpecFromSubplotSpec(
        nrows, ncols, subplot_spec=outer[1], hspace=0.3, wspace=0.35
    )

    axs = np.array(
        [[fig.add_subplot(plot_gs[i, j]) for j in range(ncols)] for i in range(nrows)]
    )

    center_width_inch = fig_width - 2 * logo_size
    left_frac = logo_size / fig_width
    center_frac = center_width_inch / fig_width
    right_frac = logo_size / fig_width

    band_gs = gridspec.GridSpecFromSubplotSpec(
        1,
        3,
        subplot_spec=outer[0],
        wspace=0,
        width_ratios=[left_frac, center_frac, right_frac],
    )
    ax_left = fig.add_subplot(band_gs[0])
    ax_center = fig.add_subplot(band_gs[1])
    ax_right = fig.add_subplot(band_gs[2])

    for ax in (ax_left, ax_center, ax_right):
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    top_band_axes = (ax_left, ax_center, ax_right)

    _add_top_band(
        top_band_axes,
    )

    return fig, axs

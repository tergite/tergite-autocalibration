'''Analyze the measured dataset and extract the qoi (quantity of interest)'''
import collections
from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import xarray as xr
import warnings

from tergite_acl.config import settings
from tergite_acl.config.coupler_config import qubit_types
from tergite_acl.lib.analysis.tof_analysis import analyze_tof
from tergite_acl.utils.post_processing_utils import manage_plots
from tergite_acl.utils.status import DataStatus

matplotlib.use(settings.PLOTTING_BACKEND)

def post_process(result_dataset: xr.Dataset, node, data_path: Path):

    if node.name == 'tof':
        tof = analyze_tof(result_dataset, True)
        return

    column_grid = 5
    fig, axs = manage_plots(result_dataset, column_grid, node.plots_per_qubit)

    qoi: list
    data_status: DataStatus

    data_vars_dict = collections.defaultdict(set)
    for var in result_dataset.data_vars:
        this_qubit = result_dataset[var].attrs['qubit']
        data_vars_dict[this_qubit].add(var)

    all_results = {}
    for indx, var in enumerate(result_dataset.data_vars):
        # this refers to the qubit whose resonator was used for the measurement
        # not necessarily the element where the settable was applied
        this_qubit = result_dataset[var].attrs['qubit']
        this_element = this_qubit

        ds = xr.Dataset()
        for var in data_vars_dict[this_qubit]:
            ds = xr.merge([ds, result_dataset[var]])

        ds.attrs['qubit'] = this_qubit
        ds.attrs['node'] = node.name

        # detect the element_type on which the settables act
        for settable in ds.coords:
            if ds[settable].attrs['element_type'] == 'coupler':
                this_element = 'coupler'

        primary_plot_row = node.plots_per_qubit * (indx // column_grid)
        primary_axis = axs[primary_plot_row, indx % column_grid]

        redis_field = node.redis_field
        analysis_kwargs = getattr(node, 'analysis_kwargs', dict())
        node_analysis = node.analysis_obj(ds, **analysis_kwargs)
        qoi = node_analysis.run_fitting()

        node_analysis.qoi = qoi

        if node.type == 'adaptive_sweep':
            # fetch relative kwargs, e.g. known minima in motzoi calibration
            qubit_adaptive_kwargs = node.adaptive_kwargs[this_qubit]
            # every adaptive iteration should update the samplespace ...
            new_qubit_samplespace = node_analysis.updated_qubit_samplespace(**qubit_adaptive_kwargs)
            for settable_key in new_qubit_samplespace.keys():
                node.samplespace[settable_key].update(new_qubit_samplespace[settable_key])
            # every adaptive iteration should also update the relevant kwargs
            node.adaptive_kwargs[this_qubit] = node_analysis.updated_kwargs
            if node.measurement_is_completed:
                node_analysis.update_redis_trusted_values(node.name, this_qubit, redis_field)

        # elif node.name in ['cz_calibration', 'cz_dynamic_phase', 'cz_calibration_ssro', 'cz_optimize_chevron'] and \
        #         qubit_types[this_qubit] == 'Target':
        #     node_analysis.update_redis_trusted_values(node.name, this_element, redis_field)
        # elif node.name in ['cz_chevron'] and qubit_types[this_qubit] == 'Control':
        #     node_analysis.update_redis_trusted_values(node.name, this_element, redis_field)
        # elif node.name in ['coupler_spectroscopy']:
        #     node_analysis.update_redis_trusted_values(node.name, this_element, redis_field)
        #     this_element = node.coupler
        # else:
        #     node_analysis.update_redis_trusted_values(node.name, this_elementredis_field)
        #     this_element = this_qubit

        node_analysis.update_redis_trusted_values(node.name, this_element, redis_field)
        all_results[this_element] = dict(zip(redis_field, qoi))

        if node.plots_per_qubit > 1:
            list_of_secondary_axes = []
            for plot_indx in range(1, node.plots_per_qubit):
                secondary_plot_row = primary_plot_row + plot_indx
                list_of_secondary_axes.append(
                    axs[secondary_plot_row, indx % column_grid]
                )
            node_analysis.plotter(primary_axis, secondary_axes=list_of_secondary_axes)
        else:
            node_analysis.plotter(primary_axis)
        handles, labels = primary_axis.get_legend_handles_labels()

        patch = mpatches.Patch(color='red', label=f'{this_qubit}')
        handles.append(patch)
        primary_axis.legend(handles=handles, fontsize='small')
        if node.plots_per_qubit > 1:
            for secondary_ax in list_of_secondary_axes:
                secondary_ax.legend()

    # figure_manager = plt.get_current_fig_manager()
    # figure_manager.window.showMaximized()
    fig = plt.gcf()
    fig.set_tight_layout(True)
    try:
        fig.savefig(f'{data_path}/{node.name}.png', bbox_inches='tight', dpi=600)
    except FileNotFoundError:
        warnings.warn('File Not existing')
        pass
    # plt.show()
    plt.show(block=True)
    # plt.pause(20)
    # plt.close()

    if node != 'tof':
        all_results.update({'measurement_dataset': result_dataset.to_dict()})

    return all_results

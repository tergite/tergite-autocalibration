'''Analyze the measured dataset and extract the qoi (quantity of interest)'''
import collections
from pathlib import Path

import matplotlib
# from quantify_core.analysis.calibration import rotate_to_calibrated_axis
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from quantify_core.data.handling import set_datadir

from tergite_acl.config import settings
from tergite_acl.config.coupler_config import qubit_types
from tergite_acl.lib.analysis.tof_analysis import analyze_tof
from tergite_acl.utils.status import DataStatus

matplotlib.use(settings.PLOTTING_BACKEND)
set_datadir('../workers')


def post_process(result_dataset: xr.Dataset, node, data_path: Path):
    # analysis = Multiplexed_Analysis(result_dataset, node, data_path)
    if node.name == 'tof':
        tof = analyze_tof(result_dataset, True)
        return

    n_vars = len(result_dataset.data_vars)
    n_coords = len(result_dataset.coords)

    fit_numpoints = 300
    column_grid = 5
    rows = int(np.ceil(n_vars / column_grid))
    rows = rows * node.plots_per_qubit

    # TODO What does this do, when the MSS is not connected?
    node_result = {}

    fig, axs = plt.subplots(
        nrows=rows,
        ncols=np.min((n_vars, n_coords, column_grid)),
        squeeze=False,
        figsize=(column_grid * 5, rows * 5)
    )

    qoi: list
    data_status: DataStatus

    data_vars_dict = collections.defaultdict(set)
    for var in result_dataset.data_vars:
        this_qubit = result_dataset[var].attrs['qubit']
        data_vars_dict[this_qubit].add(var)

    all_results = {}
    for indx, var in enumerate(result_dataset.data_vars):
        this_qubit = result_dataset[var].attrs['qubit']

        ds = xr.Dataset()
        for var in data_vars_dict[this_qubit]:
            ds = xr.merge([ds, result_dataset[var]])

        ds.attrs['qubit'] = this_qubit
        ds.attrs['node'] = node.name

        primary_plot_row = node.plots_per_qubit * (indx // column_grid)
        primary_axis = axs[primary_plot_row, indx % column_grid]

        redis_field = node.redis_field
        kw_args = getattr(node, "analysis_kwargs", dict())
        node_analysis = node.analysis_obj(ds, **kw_args)
        qoi = node_analysis.run_fitting()
        # TODO: This step should better happen inside the analysis function
        node_analysis.qoi = qoi

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

        if node.type == 'adaptive_sweep':
            new_qubit_samplespace = node_analysis.updated_qubit_samplespace()
            node.adaptive_kwargs = node_analysis.updated_kwargs()
            node.samplespace.update(new_qubit_samplespace)

        # TODO temporary hack:
        if node.name in ['cz_calibration', 'cz_dynamic_phase', 'cz_calibration_ssro', 'cz_optimize_chevron'] and \
                qubit_types[this_qubit] == 'Target':
            node_analysis.update_redis_trusted_values(node.name, node.coupler, redis_field)
            this_element = node.coupler
        elif node.name in ['cz_chevron'] and qubit_types[this_qubit] == 'Control':
            node_analysis.update_redis_trusted_values(node.name, node.coupler, redis_field)
            this_element = node.coupler
        elif node.name in ['coupler_spectroscopy']:
            node_analysis.update_redis_trusted_values(node.name, node.coupler, redis_field)
            this_element = node.coupler
        else:
            node_analysis.update_redis_trusted_values(node.name, this_qubit, redis_field)
            this_element = this_qubit

        all_results[this_element] = dict(zip(redis_field, qoi))
        handles, labels = primary_axis.get_legend_handles_labels()

        patch = mpatches.Patch(color='red', label=f'{this_qubit}')
        handles.append(patch)
        primary_axis.legend(handles=handles, fontsize='small')
        if node.plots_per_qubit > 1:
            for secondary_ax in list_of_secondary_axes:
                secondary_ax.legend()

        # logger.info(f'Analysis for the {node} of {this_qubit} is done, saved at {self.data_path}')
    # figure_manager = plt.get_current_fig_manager()
    # figure_manager.window.showMaximized()
    fig = plt.gcf()
    fig.set_tight_layout(True)
    fig.savefig(f'{data_path}/{node.name}.png', bbox_inches='tight', dpi=600)
    # plt.show()
    plt.show(block=True)
    # plt.pause(20)
    # plt.close()

    if node != 'tof':
        all_results.update({'measurement_dataset': result_dataset.to_dict()})

    return all_results

# class BaseAnalysis():
#     def __init__(self, result_dataset: xr.Dataset, node, data_path: Path):
#         self.result_dataset = result_dataset
#         self.data_path = data_path
#
#         self.n_vars = len(self.result_dataset.data_vars)
#         self.n_coords = len(self.result_dataset.coords)
#
#         self.fit_numpoints = 300
#         self.column_grid = 5
#         self.rows = int(np.ceil((self.n_vars) / self.column_grid))
#         self.rows = self.rows * node.plots_per_qubit
#
#         # TODO What does this do, when the MSS is not connected?
#         self.node_result = {}
#
#         self.fig, self.axs = plt.subplots(
#             nrows=self.rows,
#             ncols=np.min((self.n_vars, self.n_coords, self.column_grid)),
#             squeeze=False,
#             figsize=(self.column_grid * 5, self.rows * 5)
#         )
#
#         self.qoi: list
#         self.data_status: DataStatus
#
#     def update_redis_trusted_values(self, node: str, this_element: str, transmon_parameters: list):
#         for i, transmon_parameter in enumerate(transmon_parameters):
#             if '_' in this_element:
#                 name = 'couplers'
#             else:
#                 name = 'transmons'
#             redis_connection.hset(f"{name}:{this_element}", f"{transmon_parameter}", self.qoi[i])
#             redis_connection.hset(f"cs:{this_element}", node, 'calibrated')
#             self.node_result.update({this_element: self.qoi[i]})
#
#
# class Multiplexed_Analysis(BaseAnalysis):
#     def __init__(self, result_dataset: xr.Dataset, node, data_path: Path):
#         if node.name == 'tof':
#             tof = analyze_tof(result_dataset, True)
#             return
#         super().__init__(result_dataset, node, data_path)
#
#         data_vars_dict = collections.defaultdict(set)
#         for var in result_dataset.data_vars:
#             this_qubit = result_dataset[var].attrs['qubit']
#             data_vars_dict[this_qubit].add(var)
#
#         self.all_results = {}
#         for indx, var in enumerate(result_dataset.data_vars):
#             this_qubit = result_dataset[var].attrs['qubit']
#
#             ds = xr.Dataset()
#             for var in data_vars_dict[this_qubit]:
#                 ds = xr.merge([ds, result_dataset[var]])
#
#             ds.attrs['qubit'] = this_qubit
#             ds.attrs['node'] = node.name
#
#             primary_plot_row = node.plots_per_qubit * (indx // self.column_grid)
#             primary_axis = self.axs[primary_plot_row, indx % self.column_grid]
#
#             redis_field = node.redis_field
#             kw_args = getattr(node, "analysis_kwargs", dict())
#             node_analysis = node.analysis_obj(ds, **kw_args)
#             self.qoi = node_analysis.run_fitting()
#
#             if node.plots_per_qubit > 1:
#                 list_of_secondary_axes = []
#                 for plot_indx in range(1, node.plots_per_qubit):
#                     secondary_plot_row = primary_plot_row + plot_indx
#                     list_of_secondary_axes.append(
#                         self.axs[secondary_plot_row, indx % self.column_grid]
#                     )
#                 node_analysis.plotter(primary_axis, secondary_axes=list_of_secondary_axes)
#             else:
#                 node_analysis.plotter(primary_axis)
#
#             # TODO temporary hack:
#             if node.name in ['cz_calibration', 'cz_dynamic_phase', 'cz_calibration_ssro', 'cz_optimize_chevron'] and \
#                     qubit_types[this_qubit] == 'Target':
#                 self.update_redis_trusted_values(node.name, node.coupler, redis_field)
#                 this_element = node.coupler
#             elif node.name in ['cz_chevron'] and qubit_types[this_qubit] == 'Control':
#                 self.update_redis_trusted_values(node.name, node.coupler, redis_field)
#                 this_element = node.coupler
#             elif node.name in ['coupler_spectroscopy']:
#                 self.update_redis_trusted_values(node.name, node.coupler, redis_field)
#                 this_element = node.coupler
#             else:
#                 self.update_redis_trusted_values(node.name, this_qubit, redis_field)
#                 this_element = this_qubit
#
#             self.all_results[this_element] = dict(zip(redis_field, self.qoi))
#             handles, labels = primary_axis.get_legend_handles_labels()
#
#             patch = mpatches.Patch(color='red', label=f'{this_qubit}')
#             handles.append(patch)
#             primary_axis.legend(handles=handles, fontsize='small')
#             if node.plots_per_qubit > 1:
#                 for secondary_ax in list_of_secondary_axes:
#                     secondary_ax.legend()
#
#             # logger.info(f'Analysis for the {node} of {this_qubit} is done, saved at {self.data_path}')
#
#     def get_results(self):
#         return self.all_results

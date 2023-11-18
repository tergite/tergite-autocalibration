'''Analyze the measured dataset and extract the qoi (quantity of interest)'''
import collections
import matplotlib.pyplot as plt
import xarray as xr
from analysis.tof_analysis import analyze_tof
from quantify_core.data.handling import set_datadir
# from quantify_core.analysis.calibration import rotate_to_calibrated_axis
import matplotlib.patches as mpatches
import numpy as np
import redis
import matplotlib
from pathlib import Path
matplotlib.use('tkagg')
set_datadir('.')
redis_connection = redis.Redis(decode_responses=True)

def post_process(result_dataset: xr.Dataset, node, data_path: Path):
    analysis = Multiplexed_Analysis(result_dataset, node, data_path)

    # figure_manager = plt.get_current_fig_manager()
    # figure_manager.window.showMaximized()
    fig = plt.gcf()
    fig.set_tight_layout(True)
    fig.savefig(f'{data_path}/{node.name}.png', bbox_inches='tight', dpi=600)
    plt.show()
    plt.show(block=False)
    plt.pause(30)
    plt.close()

    if node != 'tof':
        analysis.node_result.update({'measurement_dataset':result_dataset.to_dict()})


class BaseAnalysis():
    def __init__(self, result_dataset: xr.Dataset, data_path: Path):
        self.result_dataset = result_dataset
        self.data_path = data_path

        self.n_vars = len(self.result_dataset.data_vars)
        self.n_coords = len(self.result_dataset.coords)

        self.fit_numpoints = 300
        self.column_grid = 5
        self.rows = int(np.ceil((self.n_vars ) / self.column_grid))

        self.node_result = {}
        self.fig, self.axs = plt.subplots(
            nrows=self.rows,
            ncols=np.min((self.n_coords, self.column_grid)),
            squeeze=False,
            figsize=(self.column_grid*5,self.rows*5)
        )
        self.qoi: list

    def update_redis_trusted_values(self, node: str, this_qubit: str, transmon_parameters: list):
        for i,transmon_parameter in enumerate(transmon_parameters):
            #print(f'{ transmon_parameter = }')
            #print(f'{ self.qoi[i] = }')
            redis_connection.hset(f"transmons:{this_qubit}", f"{transmon_parameter}", self.qoi[i])
            redis_connection.hset(f"cs:{this_qubit}", node, 'calibrated')
            self.node_result.update({this_qubit: self.qoi[i]})


class Multiplexed_Analysis(BaseAnalysis):
    def __init__(self, result_dataset: xr.Dataset, node, data_path: Path):
        if node.name == 'tof':
            tof = analyze_tof(result_dataset, True)
            return
        # print(f'{ result_dataset = }')
        super().__init__(result_dataset, data_path)
        data_vars_dict = collections.defaultdict(set)
        for var in result_dataset.data_vars:
            this_qubit = result_dataset[var].attrs['qubit']
            data_vars_dict[this_qubit].add(var)

        for indx, var in enumerate(result_dataset.data_vars):
            this_qubit = result_dataset[var].attrs['qubit']
            # ds = result_dataset[var].to_dataset()
            ds = xr.Dataset()
            for var in data_vars_dict[this_qubit]:
                ds = xr.merge([ds, result_dataset[var]])

            ds.attrs['qubit'] = this_qubit

            this_axis = self.axs[indx // self.column_grid, indx % self.column_grid]
            kw_args = {}
            # this_axis.set_title(f'{node_name} for {this_qubit}')
            redis_field = node.redis_field

            node_analysis = node.analysis_obj(ds, **kw_args)
            self.qoi = node_analysis.run_fitting()

            #if node == 'rabi_oscillations':
            #    res, stderr = node_analysis.run_fitting()
            #    self.qoi = res
            #else:
            #    self.qoi = node_analysis.run_fitting()

            node_analysis.plotter(this_axis)
            # if node.name == 'cz_chevron':
            #     print( 'REDIS UPDATE COMMENTED OUT')
            # else:

            self.update_redis_trusted_values(node.name, this_qubit, redis_field)

            handles, labels = this_axis.get_legend_handles_labels()

            if node.name == 'T1':
                T1_micros = self.qoi[0] * 1e6
                patch2 = mpatches.Patch(color='blue', label=f'T1 = {T1_micros:.2f}')
                handles.append(patch2)
            patch = mpatches.Patch(color='red', label=f'{this_qubit}')
            handles.append(patch)
            this_axis.set(title=None)
            this_axis.legend(handles=handles, fontsize='small')
            # logger.info(f'Analysis for the {node} of {this_qubit} is done, saved at {self.data_path}')

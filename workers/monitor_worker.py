import xarray
from utilities.status import ClusterStatus
from workers.compilation_worker import precompile
from workers.execution_worker import measure_node
from workers.hardware_utils import SpiDAC
from workers.post_processing_worker import post_process
from logger.tac_logger import logger
import scipy.optimize as optimize


'''
sweep types:
simple_sweep
optimized_sweep: sweep under an external parameter
parameterized_sweep: sweep under a schedule parameter e.g. T1 or RB
'''

def monitor_node_calibration(node, data_path, lab_ic):
    if node.type == 'simple_sweep':
        compiled_schedule = precompile(node)

        result_dataset = measure_node(
            node,
            compiled_schedule,
            lab_ic,
            data_path,
            cluster_status=ClusterStatus.real,
        )

        logger.info('measurement completed')
        measurement_result = post_process(result_dataset, node, data_path=data_path)
        logger.info('analysis completed')

    elif node.type == 'parameterized_sweep':
        print('Performing parameterized sweep')
        ds = xarray.Dataset()

        for node_parameter in node.node_externals:
            node.external_parameter_value = node_parameter
            print(f'{ node.external_parameter_value = }')
            compiled_schedule = precompile(node)

            result_dataset = measure_node(
                node,
                compiled_schedule,
                lab_ic,
                data_path,
                cluster_status=ClusterStatus.real,
            )

            ds = xarray.merge([ds, result_dataset])
        logger.info('measurement completed')
        measurement_result = post_process(ds, node, data_path=data_path)
        logger.info('analysis completed')

    elif node.type == 'optimized_sweep':
        print('Performing optimized Sweep')
        compiled_schedule = precompile(node)

        optimization_element = 'q13_q14'

        optimization_guess = 100e-6

        spi = SpiDAC()
        dac = spi.create_spi_dac(optimization_element)

        def set_optimizing_parameter(optimizing_parameter):
            if node.name == 'cz_chevron_optimize':
                spi.set_dac_current(dac, optimizing_parameter)


        def single_sweep(optimizing_parameter) -> float:
            set_optimizing_parameter(optimizing_parameter)

            result_dataset = measure_node(
                node,
                compiled_schedule,
                lab_ic,
                data_path,
                cluster_status=ClusterStatus.real,
            )

            measurement_result = post_process(result_dataset, node, data_path=data_path)

            optimization_quantity = measurement_result[optimization_element][node.optimization_field]

            return optimization_quantity

        optimize.minimize(
            single_sweep,
            optimization_guess,
            method='Nelder-Mead',
            bounds=[(80e-6, 120e-6)],
            options={'maxiter':2}
        )

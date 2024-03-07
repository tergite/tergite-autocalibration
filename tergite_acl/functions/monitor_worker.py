import xarray
from tergite_acl.utils.status import ClusterStatus
from tergite_acl.functions.compilation_worker import precompile
from tergite_acl.functions.execution_worker import measure_node
from tergite_acl.utils.hardware_utils import SpiDAC
from tergite_acl.functions.post_processing_worker import post_process
from tergite_acl.utils.logger.tac_logger import logger
import scipy.optimize as optimize

'''
sweep types:
cluster_simple_sweep:
   sweep on a predefined samplespace on cluster-controlled parameters.
   The schedule is compiled only once.
   At the moment, most of nodes are of this type.
spi_and_cluster_simple_sweep:
   sweep on a predefined samplespace on both
   cluster-controlled and spi-controlled parameters.
   The schedule is compiled only once. e.g. coupler spectroscopy
parameterized_simple_sweep:
   sweep under an external parameter
   The schedule is compiled only once. e.g. T1
   In T1 the external parameter is a nothing
   but still we achieve measurement repetition
TODO optimized_sweep:
    sweep under an external parameter
parameterized_sweep:
    sweep under a schedule parameter e.g. RB.
    For every external parameter value, the schedule is recompiled.
'''

def monitor_node_calibration(node, data_path, lab_ic):
    # TODO: Instead of the types there should be different node classes
    # TODO: What all nodes have in common is the precompile step
    if node.type == 'cluster_simple_sweep':
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

    elif node.type == 'parameterized_simple_sweep':
        compiled_schedule = precompile(node)
        external_parameter_values = node.node_externals
        pre_measurement_operation = node.pre_measurement_operation
        operations_args = node.operations_args

        print('Performing parameterized simple sweep')
        ds = xarray.Dataset()

        for node_parameter in external_parameter_values:
            node.external_parameter_value = node_parameter
            pre_measurement_operation(*operations_args, external=node_parameter)
            result_dataset = measure_node(
                node,
                compiled_schedule,
                lab_ic,
                data_path,
                cluster_status=ClusterStatus.real,
                measurement=(node_parameter, len(external_parameter_values))
            )
            ds = xarray.merge([ds, result_dataset])

        logger.info('measurement completed')
        measurement_result = post_process(ds, node, data_path=data_path)
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


    elif node.type == 'spi_and_cluster_simple_sweep':
        # compilation is needed only once
        compiled_schedule = precompile(node)

        external_parameter_values = node.node_externals
        pre_measurement_operation = node.pre_measurement_operation
        operations_args = node.operations_args

        ds = xarray.Dataset()
        logger.info('Starting coupler spectroscopy')

        for node_parameter in external_parameter_values:
            node.external_parameter_value = node_parameter
            pre_measurement_operation(*operations_args, external=node_parameter)

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

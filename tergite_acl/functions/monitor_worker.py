import xarray
from tergite_acl.utils.dataset_utils import retrieve_dummy_dataset
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
adaptive_sweep:
    modify the samplespace after each sweep and repeat
    For every external parameter value, the schedule is recompiled.
'''

def monitor_node_calibration(node, data_path, lab_ic, cluster_status):
    # TODO: Instead of the types there should be different node classes
    # TODO: What all nodes have in common is the precompile step
    print(f'{ node.type = }')
    if node.type == 'cluster_simple_sweep':
        compiled_schedule = precompile(node)

        result_dataset = measure_node(
            node,
            compiled_schedule,
            lab_ic,
            data_path,
            cluster_status,
        )

        if cluster_status==ClusterStatus.dummy:
            result_dataset = retrieve_dummy_dataset(result_dataset, node)

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
                cluster_status,
                measurement=(node_parameter, len(external_parameter_values))
            )
            ds = xarray.merge([ds, result_dataset])

        logger.info('measurement completed')
        measurement_result = post_process(ds, node, data_path=data_path)
        logger.info('analysis completed')



    elif node.type == 'parameterized_sweep':
        print('Performing parameterized sweep')
        ds = xarray.Dataset()

        iterations = len(node.node_externals)

        for iteration_index in range(node.external_iterations):
            if iteration_index == node.external_iterations:
                node.measurement_is_completed = True
            node_parameter = node.node_externals[iteration_index]
            node.external_parameter_value = node_parameter
            node.external_parameters = {
                node.external_parameter_name: node_parameter
            }
            # reduce the external samplespace
            compiled_schedule = precompile(node)

            result_dataset = measure_node(
                node,
                compiled_schedule,
                lab_ic,
                data_path,
                cluster_status,
            )
            if cluster_status == ClusterStatus.dummy:
                result_dataset = retrieve_dummy_dataset(result_dataset, node)
                continue

            if node.post_process_each_iteration:
                measurement_result = post_process(result_dataset, node, data_path=data_path)
            ds = xarray.merge([ds, result_dataset])

        logger.info('measurement completed')
        if not node.post_process_each_iteration:
            measurement_result = post_process(ds, node, data_path=data_path)
        logger.info('analysis completed')


    elif node.type == 'adaptive_sweep':
        print('Performing Adaptive sweep')
        ds = xarray.Dataset()

        iterations = len(node.node_externals)

        for index, node_parameter in enumerate(node.node_externals):
            node.external_parameter_value = node_parameter
            print(f'{ node.external_parameter_value = }')
            compiled_schedule = precompile(node)

            result_dataset = measure_node(
                node,
                compiled_schedule,
                lab_ic,
                data_path,
                cluster_status,
            )
            # flag the last measurement so the postprocessing stores the extracted value
            if index == iterations - 1:
                node.measurement_is_completed = True

            measurement_result = post_process(result_dataset, node, data_path=data_path)
            ds = xarray.merge([ds, result_dataset])

        logger.info('measurement completed')
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
                cluster_status,
            )

            ds = xarray.merge([ds, result_dataset])

        logger.info('measurement completed')
        measurement_result = post_process(ds, node, data_path=data_path)
        logger.info('analysis completed')

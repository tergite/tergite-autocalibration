from qblox_instruments.ieee488_2 import DummyBinnedAcquisitionData
from qblox_instruments import Cluster, ClusterType


def dummy_cluster(samplespace: dict):
    dummy = {str(mod): ClusterType.CLUSTER_QCM_RF for mod in range(1, 16)}
    dummy["16"] = ClusterType.CLUSTER_QRM_RF
    dummy["17"] = ClusterType.CLUSTER_QRM_RF
    dimension = 1
    for subspace in samplespace.values():
        dimension *= len(list(subspace.values())[0])

    dummy_data = [ DummyBinnedAcquisitionData(data=(1,6),thres=1,avg_cnt=1) for _ in range(dimension) ]
    dummy_data_1 = [ DummyBinnedAcquisitionData(data=(1,3),thres=1,avg_cnt=1) for _ in range(dimension) ]
    clusterA = Cluster("clusterA", dummy_cfg=dummy)
    clusterA.set_dummy_binned_acquisition_data(16, sequencer=0, acq_index_name="0", data=dummy_data)
    clusterA.set_dummy_binned_acquisition_data(16, sequencer=1, acq_index_name="1", data=dummy_data)
    clusterA.set_dummy_binned_acquisition_data(16, sequencer=2, acq_index_name="2", data=dummy_data)

    # if node == 'ro_frequency_optimization':
    #     clusterA.set_dummy_binned_acquisition_data(16,sequencer=0,acq_index_name="3",data=dummy_data_1)
    #     clusterA.set_dummy_binned_acquisition_data(16,sequencer=1,acq_index_name="4",data=dummy_data_1)
    #     clusterA.set_dummy_binned_acquisition_data(16,sequencer=2,acq_index_name="5",data=dummy_data_1)

    return clusterA

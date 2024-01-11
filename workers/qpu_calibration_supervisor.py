from workers.hardware_utils import SpiDAC
import numpy as np

parking_currents = np.linspace(-1e-3, 1e-3, 5)

def nullify_nodes_on_path(node_name: str):
    pass

set_module_att(clusterA)

for current in parking_currents:
    for coupler in couplers:
        spi = SpiDAC()
        spi.set_parking_current(coupler)

    nullify_nodes_on_path('cz_chevron')

    linear_supervisor('cz_chevron')


from tergite_acl.config.VNA_values import VNA_qubit_frequencies, VNA_resonator_frequencies, VNA_f12_frequencies
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from dataclasses import dataclass
import numpy as np

@dataclass
class QPU_element:
    label: str
    XY_line: str
    module: int
    grid_coords: tuple[int,int]
    def __post_init__(self):
        self.res_freq = VNA_resonator_frequencies[self.label]
        self.qubit_freq = VNA_qubit_frequencies[self.label]
        self.qubit_f12 = VNA_f12_frequencies[self.label]
        self.LO: float
        self.IF: float
        self.IF_12: float

QPU = [
#        QPU_element('q11', 'D6', 1, (0,2)),
#        QPU_element('q12', 'A1', 2, (1,2)),
#        QPU_element('q13', 'A5', 3, (2,2)),
#        QPU_element('q14', 'A9', 4, (3,2)),
#        QPU_element('q15', 'D4', 5, (4,2)),
        QPU_element('q16', 'A3', 6, (0,1)),
        QPU_element('q17', 'D2', 7, (1,1)),
        QPU_element('q18', 'A2', 8, (2,1)),
        QPU_element('q19', 'D3', 9, (3,1)),
        QPU_element('q20', 'A8', 10, (4,1)),
        QPU_element('q21', 'D5', 11, (0,0)),
        QPU_element('q22', 'A4', 12, (1,0)),
        QPU_element('q23', 'A6', 13, (2,0)),
        QPU_element('q24', 'D7', 14, (3,0)),
        QPU_element('q25', 'A7', 15,(4,0)),
      ]

# edge = {{'q11_q12':1},{'q12_q13':2},{'q13_q14':1},{'q14_q15':2},
#         {'q11_q16':3},{'q12_q17':4},{'q13_q18':3},{'q14_q19':4},{'q15_q20':3},
#         {'q16_q17':5},{'q17_q18':6},{'q18_q19':5},{'q19_q20':6},
#         {'q16_q21':7},{'q17_q22':8},{'q18_q23':7},{'q19_q24':8},{'q20_q25':7},
#         {'q21_q22':9},{'q22_q23':10},{'q23_q24':9},{'q24_q25':10},
#         }

# edge_group = [[1,6,9],[2,5,10],[3,8],[4,7]]

# edge_group = {'q11_q12':1,'q12_q13':2,'q13_q14':1,'q14_q15':2,
#         'q11_q16':3,'q12_q17':4,'q13_q18':3,'q14_q19':4,'q15_q20':3,
#         'q16_q17':2,'q17_q18':1,'q18_q19':2,'q19_q20':1,
#         'q16_q21':4,'q17_q22':3,'q18_q23':4,'q19_q24':3,'q20_q25':4,
#         'q21_q22':1,'q22_q23':2,'q23_q24':1,'q24_q25':2}

def distance(element_1, element_2) -> int:
     x_distance = np.abs(element_1.grid_coords[0] - element_2.grid_coords[0])
     y_distance = np.abs(element_1.grid_coords[1] - element_2.grid_coords[1])
     return x_distance + y_distance


LO_group = 3.511e9
LO_16 = 3.295e9
LO_17 = 4.055e9
LO_20 = 3.455e9
LO_25 = 4.124e9
LO_21 = 3.884e9
LO_22 = 3.445e9
collision_tol = 6.5e6

def hits_neighbors(qubit:str, lo_freq:float):
    for q in QPU:
        if q.label == qubit:
            element = q

    # Code by Stefan Hill:
    neighbour_qubits = list(filter(lambda element_: distance(element, element_)==1, QPU))

    # print(f'{ neighbour_qubits = }')
    f01 = VNA_qubit_frequencies[qubit]
    f12 = VNA_f12_frequencies[qubit]
    i_freq = f01 - lo_freq
    i_freq_12 = f12 - lo_freq

    element.LO = lo_freq
    element.IF = i_freq
    element.IF_12 = i_freq_12

    mirror = lo_freq - i_freq
    harmonics = {
        'mirror': mirror,
        'h_harm_2' : lo_freq - 2*i_freq,
        'h_harm_3' : lo_freq - 3*i_freq,
        'l_harm_2' : lo_freq + 2*i_freq,
        'l_harm_3' : lo_freq + 3*i_freq,
    }

    for harmonic, harmonic_freq in harmonics.items():
        if np.abs(harmonic_freq-f12) < collision_tol:
            print(f'{qubit} harmonic {harmonic} hits f12 at distance {np.abs(harmonic_freq-f12)/1e6}MHz')

    for neighbour_element in neighbour_qubits:
        neighbour_qubit = neighbour_element.label
        neighbour_f01 = VNA_qubit_frequencies[neighbour_qubit]
        neighbour_f12 = VNA_f12_frequencies[neighbour_qubit]
        for harmonic, harmonic_freq in harmonics.items():
            if np.abs(harmonic_freq-neighbour_f01) < collision_tol:
                print(f'{qubit} harmonic {harmonic} hits neighbour_f01: {neighbour_f01} of {neighbour_qubit} at distance {(neighbour_f01-harmonic_freq)/1e6}MHz')
            if np.abs(harmonic_freq-neighbour_f12) < collision_tol:
                print(f'{qubit} harmonic {harmonic} hits neighbour_f12: {neighbour_f12} of {neighbour_qubit} at distance {(neighbour_f12-harmonic_freq)/1e6}MHz')

# group_qubits = ['q11', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17','q18', 'q19', 'q20', 'q23', 'q24', 'q25']
group_qubits = ['q18', 'q19', 'q20', 'q23', 'q24', 'q25']
[hits_neighbors(q, LO_group) for q in group_qubits]

hits_neighbors('q16', LO_16)
hits_neighbors('q17', LO_17)
hits_neighbors('q21', LO_21)
hits_neighbors('q22', LO_22)
hits_neighbors('q20', LO_20)
hits_neighbors('q25', LO_25)


# fig, ax = plt.subplots(1,1, figsize=(10,6))
# for element in QPU:
#     x_coord, y_coord = element.grid_coords
#     x_coord *= 1.6
#     y_coord *= 1.6
#     ax.add_patch(Rectangle((x_coord,y_coord),1,1.2,color='dodgerblue', alpha=0.5))
#     ann_text = f'{element.label}\nmodule{element.module}\n{element.XY_line}\n'
#     ann_text += f'{element.res_freq:.3e}\nLO:{element.LO/1e9:.3f}\n{element.qubit_freq:.3e}  IF:{element.IF/1e6:.0f}\n'
#     ann_text += f'{element.qubit_f12:.3e}  IF:{element.IF_12/1e6:.0f}'
#     ann_style = {'fontsize': 14, 'fontweight': 'roman'}
#     ax.annotate(ann_text, (x_coord,y_coord), **ann_style)
# ax.set_xlim(left = 0, right = 5*1.6 - 0.6)
# ax.set_ylim(bottom = 0, top = 6)
# plt.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
# plt.show()
# fig, ax = plt.subplots(1,1, figsize=(10,4))
# for qubit, f01 in VNA_qubit_frequencies.items():
#     f12 = VNA_f12_frequencies[qubit]
#     ax.axvline(x=f01)
#     ax.axvline(x=f12)
# plt.show()
#

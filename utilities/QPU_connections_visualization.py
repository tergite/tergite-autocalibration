from config_files.VNA_values import VNA_f01_frequencies, VNA_resonator_frequencies
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from dataclasses import dataclass

@dataclass
class QPU_element:
    label: str
    XY_line: str
    module: int
    grid_coords: tuple[int,int]
    def __post_init__(self):
        self.res_freq = VNA_resonator_frequencies[self.label]
        self.qubit_freq = VNA_f01_frequencies[self.label]

QPU = [
        QPU_element('q11', 'D6', 1, (0,2)),
        QPU_element('q12', 'A1', 2, (1,2)),
        QPU_element('q13', 'A5', 3, (2,2)),
        QPU_element('q14', 'A9', 4, (3,2)),
        QPU_element('q15', 'D4', 5, (4,2)),
        QPU_element('q16', 'A3', 1, (0,1)),
        QPU_element('q17', 'D2', 2, (1,1)),
        QPU_element('q18', 'A2', 3, (2,1)),
        QPU_element('q19', 'D3', 4, (3,1)),
        QPU_element('q20', 'A8', 5, (4,1)),
        QPU_element('q21', 'D5', 6, (0,0)),
        QPU_element('q22', 'A4', 7, (1,0)),
        QPU_element('q23', 'A6', 8, (2,0)),
        QPU_element('q24', 'D7', 9, (3,0)),
        QPU_element('q25', 'A7', 10,(4,0)),
      ]

fig, ax = plt.subplots(1,1, figsize=(10,6))

for element in QPU:
    x_coord, y_coord = element.grid_coords
    x_coord *= 1.6
    y_coord *= 1.6
    ax.add_patch(Rectangle((x_coord,y_coord),1,1.2,color='dodgerblue', alpha=0.5))
    ann_text = f'{element.label}\nmodule{element.module}\n{element.XY_line}\n{element.res_freq:.3e}\n{element.qubit_freq:.3e}'
    ann_style = {'fontsize': 14, 'fontweight': 'roman'}
    ax.annotate(ann_text, (x_coord,y_coord), **ann_style)

ax.set_xlim(left = 0, right = 5*1.6 - 0.6)
ax.set_ylim(bottom = 0, top = 6)

plt.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

plt.show()

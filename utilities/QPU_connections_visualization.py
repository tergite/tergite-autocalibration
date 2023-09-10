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
        QPU_element('q15', 'E9', 1, (4,2)),
        QPU_element('q16', 'E9', 2, (0,1)),
      ]

fig, ax = plt.subplots(1,1, figsize=(10.5,8))

for element in QPU:
    ax.add_patch(Rectangle(element.grid_coords,1,1,color='yellow', alpha=0.5))
    ann_text = f'{element.label}\nmodule{element.module}\n{element.XY_line}\n{element.res_freq:.3e}\n{element.qubit_freq:.3e}'
    ann_style = {'fontsize': 18, 'fontweight': 'roman'}
    ax.annotate(ann_text, element.grid_coords, **ann_style)

ax.set_xlim(left = 0, right = 5)
ax.set_ylim(bottom = 0, top = 5)

plt.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

plt.show()

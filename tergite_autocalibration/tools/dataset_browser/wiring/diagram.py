import matplotlib.pyplot as plt
import matplotlib.patches as patches
from config import wiring

stage_spacing = 8
stages = {
    "RT": 6 * stage_spacing,
    "50K": 5 * stage_spacing,
    "4K": 4 * stage_spacing,
    "Still": 3 * stage_spacing,
    "ColdPlate": 2 * stage_spacing,
    "MXC": 1 * stage_spacing,
}


class Attenuator:
    def __init__(self, ax, line, stage, value, position):
        self.ax = ax
        self.x_position = line
        self.y_position = stages[stage]
        self.position = position
        if self.position == "above":
            self.y_position = self.y_position
        elif self.position == "below":
            self.y_position = self.y_position - 2
        width = stage_spacing / 60
        height = stage_spacing / 4
        kwargs = {"edgecolor": "black", "facecolor": "cyan", "alpha": 0.5}
        rect = patches.Rectangle(
            (self.x_position, self.y_position), width, height, **kwargs
        )
        self.ax.add_patch(rect)
        self.ax.text(
            self.x_position + width / 2,
            self.y_position + height / 2,
            value,
            verticalalignment="center",
            horizontalalignment="center",
            fontsize=14,
            color="black",
        )


class Circulator:
    def __init__(self, ax, line, stage, value, position):
        self.ax = ax
        self.x_position = line
        self.y_position = stages[stage]
        self.position = position
        if self.position == "above":
            self.y_position = self.y_position
        elif self.position == "below":
            self.y_position = self.y_position - 2
        width = stage_spacing / 60
        height = stage_spacing / 4
        kwargs = {"edgecolor": "black", "facecolor": "yellow", "alpha": 0.5}
        rect = patches.Arrow(
            self.x_position + width / 2, self.y_position, 0, height, width=0.6, **kwargs
        )
        # rect = patches.Arrow(self.x_position, self.y_position-2, width, height, **kwargs)
        self.ax.add_patch(rect)
        self.ax.text(
            self.x_position + width / 2,
            self.y_position + height / 2,
            value,
            verticalalignment="center",
            horizontalalignment="center",
            fontsize=14,
            color="black",
        )


class Line:
    line_spacing = 0.5

    def __init__(self, ax, line, components):
        self.line = line * self.line_spacing
        self.ax = ax
        self.components = components
        for stage, elements in components.items():
            for element in elements.values():
                value = element["value"]
                position = element["position"]
                if element["type"] == "attenuator":
                    Attenuator(self.ax, self.line, stage, value, position)
                if element["type"] == "circulator":
                    Circulator(self.ax, self.line, stage, value, position)

        self.ax.text(
            self.line,
            7 * stage_spacing,
            str(line),
            verticalalignment="center",
            horizontalalignment="center",
            color="blue",
            fontsize=16,
        )


# Create a figure and axis
fig, ax = plt.subplots()

for line, components in wiring.items():
    Line(ax, line, components)

# Plot horizontal dashed lines
for label, y in stages.items():
    ax.hlines(y, xmin=0, xmax=10, linestyles="dashed", color="black")
    ax.text(
        0,
        y,
        label,
        verticalalignment="center",
        horizontalalignment="right",
        color="black",
        fontsize=20,
    )

# Set limits for x-axis
ax.set_xlim(-1, 10)
ax.set_ylim(0, stage_spacing * 7)

# Show plot
plt.show()

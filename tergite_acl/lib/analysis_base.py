import abc

# TODO: we should have a conditional import depending on a feature flag here
from matplotlib import pyplot as plt

from tergite_acl.config.settings import REDIS_CONNECTION
from tergite_acl.utils.qoi import QOI


class BaseAnalysis(abc.ABC):
    """
    Base class for the analysis
    """

    def __init__(self):
        self._qoi = None

    @property
    def qoi(self) -> 'QOI':
        return self._qoi

    @qoi.setter
    def qoi(self, value: 'QOI'):
        self._qoi = value

    @abc.abstractmethod
    def run_fitting(self) -> 'QOI':
        """
        Run the fitting of the analysis function

        Returns:
            The quantity of interest as QOI wrapped object

        """
        pass

    @abc.abstractmethod
    def plotter(self, ax: 'plt.Axes'):
        """
        Plot the fitted values from the analysis

        Args:
            ax: The axis object from matplotlib to be plotted

        Returns:
            None, will just plot the fitted values

        """
        pass

    # TODO: Alternative idea would be putting the redis handling into the QOI class
    # Pros: Would be completely high-level interfaced
    # Cons: We would have to define and implement several QOI classes
    # -> It is probably not that much effort to implement several QOI classes
    # -> We could start with a BaseQOI and add more as soon as needed
    def update_redis_trusted_values(self, node: str, this_element: str, transmon_parameters: list):
        for i, transmon_parameter in enumerate(transmon_parameters):
            if '_' in this_element:
                name = 'couplers'
            else:
                name = 'transmons'
            REDIS_CONNECTION.hset(f"{name}:{this_element}", f"{transmon_parameter}", self._qoi[i])
            REDIS_CONNECTION.hset(f"cs:{this_element}", node, 'calibrated')

# This code is part of Tergite
#
# (C) Copyright Eleftherios Moschandreou 2024
# (C) Chalmers Next Labs 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import lmfit
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from tergite_autocalibration.lib.utils.functions import exponential_decay_function

class ThreeClassBoundary:
    def __init__(self, lda: LinearDiscriminantAnalysis):
        if len(lda.classes_) != 3:
            raise ValueError("The Classifcation classes are not 3.")
        A0 = lda.coef_[0][0]
        B0 = lda.coef_[0][1]
        A1 = lda.coef_[1][0]
        B1 = lda.coef_[1][1]
        A2 = lda.coef_[2][0]
        B2 = lda.coef_[2][1]
        slope0 = -A0 / B0
        slope1 = -A1 / B1
        slope2 = -A2 / B2
        intercept0 = lda.intercept_[0]
        intercept1 = lda.intercept_[1]
        intercept2 = lda.intercept_[2]
        y_intercept0 = intercept0 / B0
        y_intercept1 = intercept1 / B1
        y_intercept2 = intercept2 / B2
        self.slopes = (slope0, slope1, slope2)
        self.y_intercepts = (y_intercept0, y_intercept1, y_intercept2)

    def intersection_I(self, index_a: int, index_b: int):
        numerator = self.y_intercepts[index_a] - self.y_intercepts[index_b]
        denominator = self.slopes[index_a] - self.slopes[index_b]
        return numerator / denominator

    def intersection_Q(self, index_a: int, index_b: int):
        numerator = self.y_intercepts[index_a] - self.y_intercepts[index_b]
        denominator = self.slopes[index_a] - self.slopes[index_b]
        return (
            self.slopes[index_a] * numerator / denominator - self.y_intercepts[index_a]
        )

    def omega(self, index_a: int, index_b: int):
        """
        Be careful: angle defined in the [0,360) range
        """
        i_point = self.intersection_I(index_a, index_b)
        q_point = self.intersection_Q(index_a, index_b)
        omega_in_rad = np.arctan2(
            [q_point - self.centroid[1]], [i_point - self.centroid[0]]
        )
        omega = (np.rad2deg(omega_in_rad) + 360) % 360
        return omega[0]

    @property
    def centroid(self):
        centroid_I = (
            self.intersection_I(0, 1)
            + self.intersection_I(1, 2)
            + self.intersection_I(2, 0)
        )
        centroid_Q = (
            self.intersection_Q(0, 1)
            + self.intersection_Q(1, 2)
            + self.intersection_Q(2, 0)
        )
        return (centroid_I / 3, centroid_Q / 3)

    @property
    def omega_01(self):
        return self.omega(0, 1)

    @property
    def omega_12(self):
        return self.omega(1, 2)

    @property
    def omega_20(self):
        return self.omega(2, 0)

    def boundary_line(self, class_a, class_b) -> tuple[np.ndarray, np.ndarray]:
        i_point = self.intersection_I(class_a, class_b)
        q_point = self.intersection_Q(class_a, class_b)
        i_values = np.linspace(self.centroid[0], i_point, 100)
        boundary_slope = (q_point - self.centroid[1]) / (i_point - self.centroid[0])
        return (
            i_values,
            boundary_slope * (i_values - self.centroid[0]) + self.centroid[1],
        )

class ExpDecayModel(lmfit.model.Model):
    """
    Generate an exponential decay model that can be fit to randomized benchmarking data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(exponential_decay_function, *args, **kwargs)

        self.set_param_hint("A", vary=True)
        self.set_param_hint("B", vary=True, min=0)
        self.set_param_hint("p", vary=True, min=0)

    def guess(self, data, **kws) -> lmfit.parameter.Parameters:
        m = kws.get("m", None)

        if m is None:
            return None

        amplitude_guess = 1 / 2
        self.set_param_hint("A", value=amplitude_guess)

        offset_guess = data[-1]
        self.set_param_hint("B", value=offset_guess)

        p_guess = 0.95
        self.set_param_hint("p", value=p_guess)

        params = self.make_params()
        return lmfit.models.update_param_vals(params, self.prefix, **kws)

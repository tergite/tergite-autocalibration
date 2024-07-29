import numpy as np

from tergite_autocalibration.config.settings import REDIS_CONNECTION
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.analysis import CZ_Parametrisation_Fix_Duration_Analysis
from tergite_autocalibration.lib.nodes.coupler.cz_parametrisation.measurement import CZ_Parametrisation_Fix_Duration
from ....utils.node_subclasses import ParametrizedSweepNode

class CZ_Parametrisation_Fix_Duration_Node(ParametrizedSweepNode):
    measurement_obj = CZ_Parametrisation_Fix_Duration
    analysis_obj = CZ_Parametrisation_Fix_Duration_Analysis

    def __init__(self, name: str, couplers: list[str], **schedule_keywords):
        self.all_qubits = [q for bus in couplers for q in bus.split("_")]
        super().__init__(name, self.all_qubits, **schedule_keywords)
        self.type = "parameterized_sweep"
        self.couplers = couplers
        self.schedule_keywords = schedule_keywords
        self.backup = False

        self.redis_field = ["cz_pulse_frequency", "cz_pulse_amplitude","cz_parking_current"]
        self.node_dictionary["cz_pulse_duration"] = 120e-9 #Need to make it configurable

        #Should these sample space move to user defined inputs?
        self.schedule_samplespace = {
            "cz_pulse_amplitudes": {
                coupler: np.linspace(0.05, 0.3, 15) for coupler in self.couplers
            },
            "cz_pulse_frequencies": {
                qubit: np.linspace(-20e6, 20e6, 21) # + self.ac_freq
                for qubit in self.all_qubits
            },
        }
        self.external_samplespace = {
            "cz_parking_current": {coupler: np.arange(-1200,-600,-10)*1e-6 for coupler in self.couplers}
        }
        # Not sure which one is correcgt
        self.coupler_samplespace = self.samplespace
        self.coupler_samplespace = self.schedule_samplespace

        self.validate()

    def validate(self) -> None:
        all_coupled_qubits = []
        for coupler in self.couplers:
            all_coupled_qubits += coupler.split("_")
        if len(all_coupled_qubits) > len(set(all_coupled_qubits)):
            print("Couplers share qubits")
            raise ValueError("Improper Couplers")

    def transition_frequency(self, coupler: str):
        coupled_qubits = coupler.split(sep="_")
        q1_f01 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[0]}", "clock_freqs:f01")
        )
        q2_f01 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[1]}", "clock_freqs:f01")
        )
        q1_f12 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[0]}", "clock_freqs:f12")
        )
        q2_f12 = float(
            REDIS_CONNECTION.hget(f"transmons:{coupled_qubits[1]}", "clock_freqs:f12")
        )
        # ac_freq = np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12))
        ac_freq = np.max(
            [
                np.abs(q1_f01 + q2_f01 - (q1_f01 + q1_f12)),
                np.abs(q1_f01 + q2_f01 - (q2_f01 + q2_f12)),
            ]
        )
        ac_freq = int(ac_freq / 1e4) * 1e4
        # lo = 4.4e9 - (ac_freq - 450e6)
        # print(f'{ ac_freq/1e6 = } MHz for coupler: {coupler}')
        # print(f'{ lo/1e9 = } GHz for coupler: {coupler}')
        return ac_freq
        

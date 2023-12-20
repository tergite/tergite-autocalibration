from quantify_scheduler.backends import SerialCompiler
from quantify_scheduler.schedules.schedule import Schedule
from quantify_scheduler.enums import BinMode
from quantify_scheduler.operations.pulse_library import  SquarePulse, SetClockFrequency, DRAGPulse
from quantify_scheduler.operations.acquisition_library import SSBIntegrationComplex
from quantify_scheduler.operations.gate_library import Reset, X
from quantify_scheduler.resources import ClockResource

def s21_scan(dev, qubits, freqs, measure=0, measure_xy=0, measure_z=0, amp=1, port=1, duration=1e-6, reps=3000):
    sched = Schedule("multiplexed_resonator_spectroscopy", reps)
    q = qubits[measure]
    qxy = qubits[measure_xy]
    qz = qubits[measure_z]

    this_ro_clock = q + 'ro'

    for freq in freqs:
        sched.add_resource(ClockResource(name=this_ro_clock, freq=freq))
    root_relaxation = sched.add(Reset(*qubits), label="Reset")

    # The second for loop iterates over all frequency values in the frequency batch:
    for acq_index, ro_frequency in enumerate(freqs):
        sched.add(

            SetClockFrequency(clock=this_ro_clock, clock_freq_new=ro_frequency),
        )
        ro_pulse = sched.add(
            SquarePulse(
                duration=duration,
                amp=amp,
                port=port,
                clock=this_ro_clock,
            ),
        )

        sched.add(
            SSBIntegrationComplex(
                duration=integration_times[this_qubit],
                port=port,
                clock=this_ro_clock,
                acq_index=acq_index,
                acq_channel=acq_cha,
                bin_mode=BinMode.AVERAGE
            ),
            ref_op=ro_pulse, ref_pt="start",
            rel_time=acquisition_delays[this_qubit],
        )

        sched.add(Reset(q))


    compilation_config = dev.generate_compilation_config()
    compiler = SerialCompiler(name=f'sq_compiler')
    compiled_schedule = compiler.compile(schedule=sched, config=compilation_config)

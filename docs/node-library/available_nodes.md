# Node Library

``` mermaid
graph TD
    A[Resonator Spectroscopy] --> A1[Punchout]
    A1 --> B(Qubit Spectroscopy)
    B --> C[Rabi Oscillations]
    C --> D[Ramsey Correction]
    D --> E[Motzoi Parameter]
    E --> F[Resonator Spectroscopy 1]
    F --> C1[T1] --> C2[T2] --> C3[Randomized Benchmarking]
    F --> F1(Qubit 12 Spectroscopy) --> G(Rabi 12 Oscillations) --> G1[Resonator Spectroscopy 2]
    F --> H1(2 States Discrimination)
    G1 --> H2(3 States Discrimination)
    A --> I(Resonator spectroscopy vs current)
    B --> J(Qubit spectroscopy vs current)
    I --> J
        
    click A href "../nodes/resonator_spectroscopy_node"
    click F href "../nodes/resonator_spectroscopy_node"
    click G1 href "../nodes/resonator_spectroscopy_node"
    click A1 href "../nodes/punchout_node"
    click B href "../nodes/qubit_spectroscopy_node"
    click F1 href "../nodes/qubit_spectroscopy_node"
    click C href "../nodes/rabi_oscillations_node"
    click I href "../nodes/resonator_spectroscopy_vs_current_node"
    click J href "../nodes/qubit_spectroscopy_vs_current_node"

    style A fill:#ffe6cc,stroke:#333,stroke-width:2px
    style A1 fill:#ffe6cc,stroke:#333,stroke-width:2px
    style B fill:#ffe6cc,stroke:#333,stroke-width:2px
    style C fill:#ffe6cc,stroke:#333,stroke-width:2px
    style D fill:#ffe6cc,stroke:#333,stroke-width:2px
    style E fill:#ffe6cc,stroke:#333,stroke-width:2px
    style F fill:#ffe6cc,stroke:#333,stroke-width:2px
    style C1 fill:#ffffcc,stroke:#333,stroke-width:2px
    style C2 fill:#ffffcc,stroke:#333,stroke-width:2px
    style C3 fill:#ffffcc,stroke:#333,stroke-width:2px
    style F1 fill:#ffe6cc,stroke:#333,stroke-width:2px
    style G fill:#ffe6cc,stroke:#333,stroke-width:2px
    style G1 fill:#ffe6cc,stroke:#333,stroke-width:2px
    style H1 fill:#ffe6cc,stroke:#333,stroke-width:2px
    style H2 fill:#ffe6cc,stroke:#333,stroke-width:2px
    style I fill:#ff9999,stroke:#333,stroke-width:2px
    style J fill:#ff9999,stroke:#333,stroke-width:2px
```

## Readout Nodes

- [resonator_spectroscopy](nodes/resonator_spectroscopy_node.md)
- [punchout](nodes/punchout_node.md)
- [resonator_spectroscopy_1](nodes/resonator_spectroscopy_node.md)
- [resonator_spectroscopy_2](nodes/resonator_spectroscopy_node.md)
- ro_frequency_two_state_optimization
- ro_frequency_three_state_optimization
- ro_amplitude_two_state_optimization
- ro_amplitude_three_state_optimization

## Qubit Control Nodes

- [qubit_01_spectroscopy](nodes/qubit_spectroscopy_node.md)
- [rabi_oscillations](nodes/rabi_oscillations_node.md)
- ramsey_correction
- [qubit_12_spectroscopy](nodes/qubit_spectroscopy_node.md)
- [rabi_oscillations_12](nodes/rabi_oscillations_node.md)
- ramsey_correction_12
- adaptive_motzoi_parameter
- n_rabi_oscillations

## Coupler Nodes

- [coupler_spectroscopy](nodes/qubit_spectroscopy_vs_current_node.md)
- [coupler_resonator_spectroscopy](nodes/resonator_spectroscopy_vs_current_node.md)

## Characterization Nodes

- T1
- T2
- T2_echo
- randomized_benchmarking
- all_XY

--8<-- "docs/node-library/redis_variable_names.md"
The Cz Chevron node sweeps the frequency and the duration of the AC flux pulse.
The amplitude of the flux pulse as well as the bias DC current are at fixed values determined by the
previous node (cz_parametrization)

The measurement is done with 3 state readout while the three state discriminator had already been found from the `ro_ampl_three_state_optimization` node.

This measurement displays the (frequency-duration) working points as yellow dots. Each dot represent a parameter pair for the flux
pulse that mediates a full return to the  $\left(|11\rangle$ state. Each point is found by a sinusoidal fit on a vertical (fixed frequency) slice. Then, all the working points are fitted to a simple parabola in order to determine the chevron vertex. The working pairs are then 
reduced to a smaller number of points adjacent to the vertex (stars in the graph) in order to simplify the next node (cz_calibration)
<figure markdown>
![cz_chevron](./cz_chevron.png){ title="the (frequency-duration) pairs that mediate a full return
    to the $\left(|11\rangle$ state" alt="cz chevron working points" }
<figcaption>Working points determined from the cz chevron graph.</figcaption>
</figure>

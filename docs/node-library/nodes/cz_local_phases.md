## Calibrate local phases:

<!-- ::: {layout-ncol=2} -->
<!---->
<!-- ![](cz_calib_schedule_Gate_on_swap_off.png){height=400} -->
<!---->
<!-- ![](cz_calib_schedule_Gate_off_swap_off.png){height=400} -->
<!---->
<!-- ::: -->

$CPh\left|0\right\rangle \left|0\right\rangle =\left|0\right\rangle \left|0\right\rangle$

$CPh\left|0\right\rangle \left|1\right\rangle =e^{-\imath\phi_{01}}\left|0\right\rangle \left|1\right\rangle$

$CPh\left|1\right\rangle \left|0\right\rangle =e^{-\imath\phi_{10}}\left|1\right\rangle \left|0\right\rangle$

$CPh\left|1\right\rangle \left|1\right\rangle =e^{-\imath\left(\phi_{01}+\phi_{10}+\phi_{g}\right)}\left|1\right\rangle \left|1\right\rangle$

$X90_{\phi}\left|0\right\rangle =$$\left(\begin{array}{cc}
1 & -\imath e^{-\imath\phi}\\
-\imath e^{\imath\phi} & 1
\end{array}\right)\left(\begin{array}{c}
1\\
0
\end{array}\right)=\left(\begin{array}{c}
1\\
-\imath e^{\imath\phi}
\end{array}\right)=\left|0\right\rangle -\imath e^{\imath\phi}\left|1\right\rangle$

$X90_{\phi}\left|1\right\rangle =\left(\begin{array}{cc}
1 & -\imath e^{-\imath\phi}\\
-\imath e^{\imath\phi} & 1
\end{array}\right)\left(\begin{array}{c}
0\\
1
\end{array}\right)=\left(\begin{array}{c}
-\imath e^{-\imath\phi}\\
1
\end{array}\right)=-\imath e^{-\imath\phi}\left|0\right\rangle +\left|1\right\rangle$

### Target Qubit Local Phase

### CZ ON

\begin{align*}
\left(X90\left|0\right\rangle \right)\left|0\right\rangle  & =\frac{1}{\sqrt{2}}\left(\left|0\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|0\right\rangle \right)\\
 & \rightarrow\\
 & \frac{1}{\sqrt{2}}Cph_{(\phi_{g})}\left(\left|0\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|0\right\rangle \right)=\frac{1}{\sqrt{2}}\left(\left|0\right\rangle \left|0\right\rangle -\imath e^{-\imath\phi_{10}}\left|1\right\rangle \left|0\right\rangle \right)\\
 & \rightarrow\\
 & \frac{1}{\sqrt{2}}X90_{\phi}^{c}\left(\left|0\right\rangle \left|0\right\rangle -\imath e^{-\imath\phi_{10}}\left|1\right\rangle \left|0\right\rangle \right)=\left[\left(\left|0\right\rangle -\imath e^{\imath\phi}\left|1\right\rangle \right)\left|0\right\rangle -\imath e^{-\imath\phi_{10}}\left(-\imath e^{-\imath\phi}\left|0\right\rangle +\left|1\right\rangle \right)\left|0\right\rangle \right]\\
 & =\left|0\right\rangle \left|0\right\rangle -\imath e^{\imath\phi}\left|1\right\rangle \left|0\right\rangle -e^{-\imath\phi}e^{-\imath\phi_{10}}\left|0\right\rangle \left|0\right\rangle -\imath e^{-\imath\phi_{10}}\left|1\right\rangle \left|0\right\rangle \\
 & =\left(1-e^{-\imath\left(\phi+\phi_{10}\right)}\right)\left|0\right\rangle \left|0\right\rangle -\imath e^{\imath\phi}\left(1+e^{-\imath\left(\phi_{10}+\phi\right)}\right)\left|1\right\rangle \left|0\right\rangle \\
\\
\end{align*}

\begin{align*}
P^{1;control} & =\left(1+e^{-\imath\left(\phi_{10}+\phi\right)}\right)\left(1+e^{+\imath\left(\phi_{10}+\phi\right)}\right)\\
 & =\left(1+e^{+\imath\left(\phi_{10}+\phi\right)}+e^{-\imath\left(\phi_{10}+\phi\right)}+1\right)\\
 & =\boxed{\frac{1}{2}\left(1+\cos\left(\phi_{10}+\phi\right)\right)}
\end{align*}

### CZ OFF

\begin{align*}
\left(X90\left|0\right\rangle \right)\left|0\right\rangle  & =\frac{1}{\sqrt{2}}\left(\left|0\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|0\right\rangle \right)\\
 & \rightarrow\\
 & \frac{1}{\sqrt{2}}\left(X90_{\phi}^{c}\left|0\right\rangle \left|0\right\rangle -\imath X90_{\phi}^{c}\left|1\right\rangle \left|0\right\rangle \right)\\
 & =\frac{1}{\sqrt{2}}\left[\left(X90_{\phi}^{c}\left|0\right\rangle \right)\left|0\right\rangle -\imath\left(X90_{\phi}^{c}\left|1\right\rangle \right)\left|0\right\rangle \right]\\
 & =\frac{1}{\sqrt{2}}\left[\left(\left|0\right\rangle -\imath e^{\imath\phi}\left|1\right\rangle \right)\left|0\right\rangle -\imath\left(-\imath e^{-\imath\phi}\left|0\right\rangle +\left|1\right\rangle \right)\left|0\right\rangle \right]\\
 & =\frac{1}{\sqrt{2}}\left[\left|0\right\rangle \left|0\right\rangle -\imath e^{\imath\phi}\left|1\right\rangle \left|0\right\rangle -e^{-\imath\phi}\left|0\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|0\right\rangle \right]\\
 & =\frac{1}{\sqrt{2}}\left[\left(1-e^{-\imath\phi}\right)\left|0\right\rangle \left|0\right\rangle -\imath\left(1+e^{\imath\phi}\right)\left|1\right\rangle \left|0\right\rangle \right]\\
\end{align*}
 \\
\begin{align*}
P^{1;control} & =\frac{1}{4}\left(1+e^{\imath\phi}\right)\left(1+e^{-\imath\phi}\right)=\frac{1}{2}\left(2+e^{-\imath\phi}+e^{\imath\phi}\right)\\
 & =\frac{1}{4}\left(2+2\cos\phi\right)=\boxed{\frac{1}{2}\left(1+\cos\phi\right)}
\end{align*}

### Repeat with swaping control_qubit $\leftrightarrow$ target_qubit



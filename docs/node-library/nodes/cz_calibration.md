For each working point: (frequency, duration) perform cz calibration

Definitions:

$X\left|0\right\rangle =\left|1\right\rangle$

$X90=\left(\begin{array}{cc} 1 & -\imath\\
-\imath & 1 \end{array}\right)$

$X90_{\phi}=\left(\begin{array}{cc} 1 & -\imath e^{-\imath\phi}\\
-\imath e^{\imath\phi} & 1 \end{array}\right)$

$X90\left|0\right\rangle =\left(\begin{array}{cc} 1 & -\imath\\
-\imath & 1 \end{array}\right)\left(\begin{array}{c} 1\\
0
\end{array}\right)=\frac{1}{\sqrt{2}}\left(\begin{array}{c}
1\\
-\imath
\end{array}\right)=\frac{1}{\sqrt{2}}\left(\left|0\right\rangle -\imath\left|1\right\rangle \right)$

$X90\left|1\right\rangle =\left(\begin{array}{cc} 1 & -\imath\\
-\imath & 1 \end{array}\right)\left(\begin{array}{c} 0\\
1
\end{array}\right)=\frac{1}{\sqrt{2}}\left(\begin{array}{c}
-\imath\\
1
\end{array}\right)=\frac{1}{\sqrt{2}}\left(-\imath\left|0\right\rangle +\left|1\right\rangle \right)$

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

$CPh\left|0\right\rangle \left|0\right\rangle =\left|0\right\rangle \left|0\right\rangle$

$CPh\left|0\right\rangle \left|1\right\rangle =\left|0\right\rangle \left|1\right\rangle$

$CPh\left|1\right\rangle \left|0\right\rangle =\left|1\right\rangle \left|0\right\rangle$

$CPh\left|1\right\rangle \left|1\right\rangle =e^{\imath\delta}\left|1\right\rangle \left|1\right\rangle$


<!-- ![](cz_calib_schedule.svg){height=400} -->

Control ON

**First operation apply X on control and X90 on target**:
\begin{align*}
X\left|0\right\rangle X90\left|0\right\rangle  & =\frac{1}{\sqrt{2}}\left|1\right\rangle \left(\left|0\right\rangle -\imath\left|1\right\rangle \right)\\
 & =\left|1\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|1\right\rangle 
\end{align*}

**Second operation apply CZ**:
$$CPh\left(\left|1\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|1\right\rangle \right)=e^{\imath\delta}\left(\left|1\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|1\right\rangle \right)$$

**Third operation apply X on control and sweep ramsey phase on target**:
\begin{align*}
X^{c}X90_{\phi}^{t}e^{\imath\delta}\left(\left|1\right\rangle \left|0\right\rangle -\imath\left|1\right\rangle \left|1\right\rangle \right) & =e^{\imath\delta}\left(X\left|1\right\rangle X90_{\phi}\left|0\right\rangle -\imath X\left|1\right\rangle X90_{\phi}\left|1\right\rangle \right)\\
 & =e^{\imath\delta}\left(\left(1-e^{-\imath\phi}\right)\left|0\right\rangle \left|0\right\rangle -\imath\left(1+e^{\imath\phi}\right)\left|0\right\rangle \left|1\right\rangle \right)\\
& =\left[\left(1-e^{\imath\delta-\imath\phi}\right)\left|0\right\rangle \left|0\right\rangle -\imath e^{\imath\delta}\left(1+e^{\imath\phi-\imath\delta}\right)\left|0\right\rangle \left|1\right\rangle \right]
\end{align*}

\begin{align*}
p_{target:1} & =\left(1+e^{\imath\left(\delta-\phi\right)}\right)\left(1+e^{-\imath\left(\delta-\phi\right)}\right)=2+e^{\imath\left(\delta-\phi\right)}+e^{-\imath\left(\delta-\phi\right)}\\
 & =1/2+e^{\imath\left(\delta-\phi\right)}-e^{-\imath\left(\delta-\phi\right)}=\boxed{1/2(1+\cos\left(\delta-\phi\right))}
\end{align*}



<!-- ![](cz_calib_schedule_OFF.svg){height=400} -->

Control OFF

\begin{align*}
\left|0\right\rangle X90\left|0\right\rangle  & =\frac{1}{\sqrt{2}}\left|0\right\rangle \left(\left|0\right\rangle -\imath\left|1\right\rangle \right)\\
 & =\left|0\right\rangle \left|0\right\rangle -\imath\left|0\right\rangle \left|1\right\rangle 
\end{align*}

$$CPh\left(\left|0\right\rangle \left|0\right\rangle -\imath\left|0\right\rangle \left|1\right\rangle \right)=\left|0\right\rangle \left|0\right\rangle -\imath\left|0\right\rangle \left|1\right\rangle$$

\begin{align*}
X90_{\phi}^{t}\left(\left|0\right\rangle \left|0\right\rangle -\imath\left|0\right\rangle \left|1\right\rangle \right) & =\left(\left|0\right\rangle X90_{\phi}\left|0\right\rangle -\imath\left|0\right\rangle X90_{\phi}\left|1\right\rangle \right)\\
 & =\left[\left(1-e^{-\imath\phi}\right)\left|0\right\rangle \left|0\right\rangle -\imath\left(1+e^{\imath\phi}\right)\left|0\right\rangle \left|1\right\rangle \right]
\end{align*}

\begin{align*}
p_{target:1} & =1/2\left(1+e^{-\imath\phi}\right)\left(1+e^{+\imath\phi}\right)\\
 & =1/2+e^{-\imath\phi}+e^{+\imath\phi}=1/2+\cos{\left(\phi\right)}\\
 & =\boxed{1/2(1+\cos{\left(\phi\right))}}
\end{align*}


<!-- ::: {.r-stack} -->
<!---->
<!-- ![](calib2.png){.fragment width=1600} -->
<!---->
<!-- ![](calib3.png){.fragment width=1600} -->
<!---->
<!-- ![](calib4.png){.fragment width=1600} -->
<!---->
<!-- ![](calib5.png){.fragment width=1600} -->
<!-- ::: -->


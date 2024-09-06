def exponential_decay_function(m: float, p: float, A: float, B: float) -> float:
    """
    Exponential decay function.
    :param m: Exponent base.
    :param p: Decay factor.
    :param A: Amplitude.
    :param B: Offset.
    :return: Result of the exponential decay function.
    """
    return A * p**m + B
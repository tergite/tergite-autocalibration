class NoValidCombinationException(Exception):
    """Exception raised when no valid combination is found."""
    def __init__(self, message="No valid combination found"):
        self.message = message
        super().__init__(self.message)
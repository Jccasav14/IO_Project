class LPError(Exception):
    pass

class InfeasibleError(LPError):
    pass

class UnboundedError(LPError):
    pass

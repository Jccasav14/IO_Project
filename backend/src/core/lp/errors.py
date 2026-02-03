class LPError(Exception):
    # Clase base para errores de PL
    pass

class InfeasibleError(LPError):
    # Se lanza cuando el modelo no tiene solucion factible
    pass

class UnboundedError(LPError):
    # Se lanza cuando la funcion objetivo es no acotada
    pass

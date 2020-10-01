import inspect

procedures = inspect.namedtuple(
    "Procedures",
    ("ProcControl", "ProcStream")
        
)

# Coexistirán procedimientos locales, que solo pueden ser accedidos a
# través de la misma entidad que los creó y los globales donde
# cualquier servicio puede disponer de ellos.
proc_scope = inspect.namedtuple("Procedures", ("locals", "globals"))

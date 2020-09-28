from inspect import namedtuple

key_repr = lambda prefix: namedtuple(
    "%s25519" % (prefix), ("public", "private")
    
)

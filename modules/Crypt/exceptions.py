class invalid_key(Exception):
    """
    En caso de que se requiera una clave pública y se obtenga una
    clave privada, generaría un error y viceversa.
    """

def remove(string: str, char: str) -> str:
    """Remover caracteres repetidos
    
    Args:
        string:
          La cadena a usar

        char:
          El carácter a remover de la cadena

    Returns:
        La nueva cadena modificada
    """

    new_string = []
    bit = False

    if (string.count(char) == 0):
        return string

    try:
        while (string[len(string)-1] == char):
            string = string[:len(string)-1]

    except IndexError:
        return char

    for _ in string.split(char):
        if (_):
            if (string[0] == char) or (bit):
                new_string.append(char)
            
            else:
                bit = True

            new_string.append(_)

    return "".join(new_string)

def remove(string: str, char: str):
    new_string = []
    bit = False

    if (string.count(char) == 0):
        return string

    while (string[len(string)-1] == char):
        string = string[:len(string)-1]

    for _ in string.split(char):
        if (_):
            if (string[0] == char) or (bit):
                new_string.append(char)
            
            else:
                bit = True

            new_string.append(_)

    return ''.join(new_string)

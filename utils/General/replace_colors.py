colors = {
    "black"  : "\033[30m",
    "red"    : "\033[1;31m",
    "green"  : "\033[1;32m",
    "yellow" : "\033[1;33m",
    "blue"   : "\033[1;34m",
    "pink"   : "\033[1;35m",
    "cyan"   : "\033[1;36m",
    "white"  : "\033[1;37m",
    "null"   : "\033[0m"

}

def replace(string):
    for const, value in colors.items():
        string = string.replace(
            "{%s}" % (const), value

        )

    return string

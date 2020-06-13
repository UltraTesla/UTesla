def generate(hosts):
    # Escapamos los '.' de las direcciones IPs
    hosts = hosts.strip().replace('.', '\.')

    # Si el módulo está instalado
    try:
        import netifaces
        from socket import gethostbyaddr # Para la búsqueda inversa

    except ModuleNotFoundError:
        return hosts

    else:
        interfaces = netifaces.interfaces()
        addresses = []
        hostnames = []

        for interface in interfaces:
            iface_info = netifaces.ifaddresses(interface)

            try:
                for iface in iface_info[netifaces.AF_INET]:
                    addr = iface['addr']
                    hostname = gethostbyaddr(addr)[0]

                    if not (addr in addresses):
                        addresses.append(addr)

                    if not (hostname in hostnames):
                        hostnames.append(hostname)

            except KeyError:
                pass

        new_hosts = '|'.join(
            addresses + hostnames

        ).replace('.', '\.')

        if (hosts):
            return '(%s|(%s))' % (hosts, new_hosts)

        else:
            return '(%s)' % (new_hosts)

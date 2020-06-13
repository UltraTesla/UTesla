import gettext

def create(domain, localedir, language):
    return gettext.translation(
        domain,
        localedir,
        [language],
        fallback=True

    ).gettext

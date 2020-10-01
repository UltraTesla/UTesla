import gettext

from utils.General import parse_config

translation_config = parse_config.parse()["Languages"]

def create(
    domain,
    localedir = translation_config["localedir"],
    language = translation_config["language"],
    install = False
    
):
    translation = gettext.translation(
        domain,
        localedir,
        [language],
        fallback=True

    )

    if (install):
        translation.install()

    return translation.gettext

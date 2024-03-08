
"""Denormalize numbers, given normalized input.
"""
from . import lang_EN_US
from . import lang_ES_US
from . import lang_FR_FR


CONVERTER_CLASSES = {
    'en': lang_EN_US.evaluate,
    'en_US': lang_EN_US.evaluate,
    'es': lang_ES_US.evaluate,
    'es_US': lang_ES_US.evaluate,
    'es_MX': lang_ES_US.evaluate,
    'fr': lang_FR_FR.evaluate,
    'fr_BE': lang_FR_FR.evaluate,
    'fr_CA': lang_FR_FR.evaluate,
    'fr_CH': lang_FR_FR.evaluate,
    'fr_FR': lang_FR_FR.evaluate,
    'fr_LU': lang_FR_FR.evaluate,
    'fr_MC': lang_FR_FR.evaluate,
}


def w2n(text, lang='en'):
    # try the full language first
    if lang not in CONVERTER_CLASSES:
        # then try first 2 letters
        lang = lang[:2]
    if lang not in CONVERTER_CLASSES:
        raise NotImplementedError()
    convert = CONVERTER_CLASSES[lang]
    return convert(text)

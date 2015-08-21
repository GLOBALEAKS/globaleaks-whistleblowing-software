# -*- coding: UTF-8
#   structures
#   **********
#
# This file contains the complex structures stored in Storm table
# in order to checks integrity between exclusive options, provide defaults,
# supports extensions (without changing DB format)

from globaleaks.models import Model
from globaleaks.settings import GLSetting

# Localized strings utility management

class Rosetta(object):
    """
    This Class can manage all the localized strings inside
    one Storm object. AKA: manage three language on a single
    stone. Hell fucking yeah, History!
    """

    def __init__(self, keys):
        self._localized_strings = {}
        self._localized_keys = keys

    def acquire_storm_object(self, obj):
        self._localized_strings = {
            key: getattr(obj, key) for key in self._localized_keys
        }

    def acquire_multilang_dict(self, obj):
        self._localized_strings = {
            key: obj[key] for key in self._localized_keys
        }

    def singlelang_to_multilang_dict(self, obj, language):
        ret = {
            key: {language: obj[key]} for key in self._localized_keys
        }

        return ret

    def dump_localized_key(self, key, language):
        default_language = GLSetting.memory_copy.default_language

        if key not in self._localized_strings:
            return ""

        translated_dict = self._localized_strings[key]

        if not isinstance(translated_dict, dict):
            return ""

        if language in translated_dict:
            return translated_dict[language]
        elif default_language in translated_dict:
            return translated_dict[default_language]
        else:
            return ""

def fill_localized_keys(dictionary, keys, language):
    mo = Rosetta(keys)

    multilang_dict = mo.singlelang_to_multilang_dict(dictionary, language)

    for key in keys:
        dictionary[key] = multilang_dict[key]

    return dictionary

def get_localized_values(dictionary, obj, keys, language):
    mo = Rosetta(keys)

    if isinstance(obj, dict):
        mo.acquire_multilang_dict(obj)
    elif isinstance(obj, Model):
        mo.acquire_storm_object(obj)

    for key in keys:
        dictionary[key] = mo.dump_localized_key(key, language)

    return dictionary


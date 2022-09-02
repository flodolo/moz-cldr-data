#! /usr/bin/env python

from glob import glob
import json
import os
import sys

# Path to this script
script_folder = os.path.abspath(os.path.dirname(__file__))

# Path to local clone of https://github.com/unicode-cldr/cldr-localenames-full
cldr_path = os.path.join(script_folder, "node_modules", "cldr-core", "supplemental")

# Path to folder containing clones from http://hg.mozilla.org/l10n-central
l10n_path = "/Users/flodolo/mozilla/mercurial/l10n_clones/locales"

# Path to clone of https://hg.mozilla.org/l10n/gecko-strings
en_path = "/Users/flodolo/mozilla/mercurial/gecko-strings-quarantine"

# You should run this script in a virtualenv, after installing requirements
from compare_locales import plurals as cl_plurals
from fluent.migrate import cldr


def main():
    # Get the list of l10n repositories
    moz_locales = []
    for locale_path in glob("{}/*/".format(l10n_path)):
        moz_locales.append(os.path.basename(os.path.normpath(locale_path)))
    moz_locales.sort()

    # Read CLDR plurals data
    with open(os.path.join(cldr_path, "plurals.json")) as data_file:
        json_data = json.load(data_file)
    cldr_plurals = json_data["supplemental"]["plurals-type-cardinal"]

    for locale in moz_locales:
        # Check locale in compare-locales
        if locale not in cl_plurals.CATEGORIES_BY_LOCALE:
            # print('{} is not supported by compare-locales'.format(locale))
            continue

        # Check locale in CLDR
        supported = False
        if locale in cldr_plurals:
            supported = True
        else:
            # Try removing the region
            fallback_locale = locale.split("-")[0]
            if fallback_locale in cldr_plurals:
                supported = True
        if not supported:
            # print('{} is not supported by CLDR'.format(locale))
            continue

        # Compare the number of forms
        if (
            cldr.get_plural_categories(locale)
            != cl_plurals.CATEGORIES_BY_LOCALE[locale]
        ):
            print("Locale: {}".format(locale))
            print("CLDR")
            print(cldr.get_plural_categories(locale))
            print("compare-locales")
            print(cl_plurals.CATEGORIES_BY_LOCALE[locale])


if __name__ == "__main__":
    main()

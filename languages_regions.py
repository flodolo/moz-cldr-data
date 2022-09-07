#! /usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from glob import glob
from urllib.request import urlopen
import json
import os
import sys
from compare_locales import parser


def parse_file(file_path, storage):
    file_extension = os.path.splitext(file_path)[1]
    file_parser = parser.getParser(file_extension)
    file_parser.readFile(file_path)
    try:
        entities = file_parser.parse()
        for entity in entities:
            # Ignore Junk
            if isinstance(entity, parser.Junk):
                continue
            if entity.raw_val is not None:
                storage[str(entity)] = entity.raw_val
    except Exception as e:
        print(f"Error parsing file: {file_path}")
        print(e)


def parse_content(file_content, storage):
    file_parser = parser.getParser(".ftl")
    file_parser.readContents(file_content)
    try:
        entities = file_parser.parse()
        for entity in entities:
            # Ignore Junk
            if isinstance(entity, parser.Junk):
                continue
            if entity.raw_val is not None:
                storage[str(entity)] = entity.raw_val
    except Exception as e:
        print(f"Error parsing remote file.")
        print(e)


def main():
    # Path to this script
    script_folder = os.path.abspath(os.path.dirname(__file__))

    # Path to clone of https://hg.mozilla.org/l10n/gecko-strings
    l10n_path = "/Users/flodolo/mozilla/mercurial/l10n_clones/locales/{}"

    # This array is used to map a Mozilla code to CLDR, e.g.
    # 'es-ES': 'es'
    locale_mapping = {
        "bn-BD": "bn",
        "en-US": "en",
        "es-ES": "es",
        "fy-NL": "fy",
        "ga-IE": "ga",
        "gu-IN": "gu",
        "hi-IN": "hi",
        "hy-AM": "hy",
        "ja-JP-mac": "ja",
        "nb-NO": "nb",
        "ne-NP": "ne",
        "nn-NO": "nn",
        "pa-IN": "pa",
        "pt-BR": "pt",
        "sv-SE": "sv",
        "zh-CN": "zh-Hans",
        "zh-TW": "zh-Hant",
    }

    # This array is used to export comparison data to CSV
    csv_rows = []

    # Get the list of l10n repositories
    moz_locales = []
    for locale_path in glob("{}/*/".format(l10n_path.replace("/{}", ""))):
        moz_locales.append(os.path.basename(os.path.normpath(locale_path)))
    moz_locales.sort()

    # Read languages from en-US
    moz_languages = {}
    url = "https://hg.mozilla.org/mozilla-central/raw-file/tip/toolkit/locales/en-US/toolkit/intl/languageNames.ftl"
    try:
        response = urlopen(url)
        file_content = response.read()
        parse_content(file_content, moz_languages)
    except Exception as e:
        sys.exit(f"Error reading remote regionNames.ftl: {e}")

    # Read languages from CLDR
    cldr_localenames_path = os.path.join(
        script_folder, "node_modules", "cldr-localenames-full", "main"
    )
    with open(os.path.join(cldr_localenames_path, "en", "languages.json")) as data_file:
        json_data = json.load(data_file)
    cldr_languages = json_data["main"]["en"]["localeDisplayNames"]["languages"]
    # Check for missing languages in CLDR
    missing_languages = []
    different_values_lang = []
    for locale, language in moz_languages.items():
        # language-name-it -> it
        # language-name-mk-2022 -> mk
        locale = locale.replace("language-name-", "").split("-")[0]
        if locale not in cldr_languages:
            missing_languages.append(f"{locale}: {language}")
        elif language != cldr_languages[locale]:
            different_values_lang.append(
                f"{locale}\n  CLDR: {cldr_languages[locale]}\n  Mozilla: {language}"
            )

    missing_languages.sort()
    if missing_languages:
        print("\nMissing language names in CLDR:")
        print("\n".join(missing_languages))
    different_values_lang.sort()
    if different_values_lang:
        print("\nDifferent values:")
        print("\n".join(different_values_lang))

    # Read regions from en-US
    moz_regions = {}
    url = "https://hg.mozilla.org/mozilla-central/raw-file/tip/toolkit/locales/en-US/toolkit/intl/regionNames.ftl"
    try:
        response = urlopen(url)
        file_content = response.read()
        parse_content(file_content, moz_regions)
    except Exception as e:
        sys.exit(f"Error reading remote regionNames.ftl: {e}")

    # Read regions from CLDR
    with open(
        os.path.join(cldr_localenames_path, "en", "territories.json")
    ) as data_file:
        json_data = json.load(data_file)
    cldr_regions = json_data["main"]["en"]["localeDisplayNames"]["territories"]
    # Check for missing regions in CLDR
    missing_regions = []
    different_values_reg = []
    for region_code, region_name in moz_regions.items():
        region_code = region_code.replace("region-name-", "").split("-")[0].upper()
        if region_code not in cldr_regions:
            missing_regions.append(f"{region_code}: {region_name}")
        elif region_name != cldr_regions[region_code]:
            # Antigua & Barbuda = Antigua and Barbuda
            if region_name == cldr_regions[region_code].replace("&", "and"):
                continue
            # Saint Barthelemy = St. Barthelemy
            if region_name == cldr_regions[region_code].replace("St.", "Saint"):
                continue

            different_values_reg.append(
                f"{region_code}\n  CLDR: {cldr_regions[region_code]}\n  Mozilla: {region_name}"
            )

    missing_regions.sort()
    if missing_regions:
        print("\nMissing region names in CLDR:")
        print("\n".join(missing_regions))
    different_values_reg.sort()
    if different_values_reg:
        print("\nDifferent values:")
        print("\n".join(different_values_reg))

    row = [
        "en-US (en)",
        len(moz_languages),
        len(different_values_lang),
        round(len(different_values_lang) / float(len(moz_languages)) * 100, 2)
        if len(moz_languages) > 0
        else 0,
        len(moz_regions),
        len(different_values_reg),
        round(len(different_values_reg) / float(len(moz_regions)) * 100, 2)
        if len(moz_regions) > 0
        else 0,
    ]
    csv_rows.append(",".join(map(str, row)))

    # Check if there are Mozilla locales missing from CLDR
    cldr_supported_locales = []
    for locale_path in glob("{cldr_localenames_path}/*/"):
        cldr_supported_locales.append(os.path.basename(os.path.normpath(locale_path)))
    cldr_supported_locales.sort()

    missing_locales = []
    missing_moz_locales = []
    # Read CLDR Seed locales from local TXT file
    seed_locales = []
    seed_file = open(os.path.join(script_folder, "data", "seed_locales.txt"))
    for line in seed_file:
        seed_locales.append(line.rstrip())
    seed_locales.sort()

    for locale in moz_locales:
        # Remove the region code
        locale_code = locale.split("-")[0]

        if locale_mapping.get(locale, locale) not in cldr_supported_locales:
            if locale in seed_locales:
                missing_locales.append(f"{locale} (available in seed)")
            elif locale_code in seed_locales:
                missing_locales.append(f"{locale} (available in seed as {locale_code})")
            else:
                missing_locales.append(locale)
        if locale_code not in moz_languages:
            missing_moz_locales.append(locale)
    missing_locales.sort()
    missing_moz_locales.sort()
    if missing_locales:
        print("\nLocales not supported by CLDR:")
        print("\n".join(missing_locales))
    if missing_moz_locales:
        print("\nMissing locales in languageNames.ftl:")
        print("\n".join(missing_moz_locales))

    # Compare data for all locales
    for locale in moz_locales:
        # Ignore locales not available in CLDR
        if locale_mapping.get(locale, locale) not in cldr_supported_locales:
            continue

        print("\n-----\nLOCALE: {locale}")

        # Read languages from Mozilla repository
        moz_languages = {}
        different_values_lang = []
        l10n_file = os.path.join(
            l10n_path.format(locale),
            "toolkit",
            "chrome",
            "global",
            "languageNames.ftl",
        )
        if os.path.isfile(l10n_file):
            parse_file(l10n_file, moz_languages)

            # Read languages from CLDR
            cldr_localenames_path = os.path.join(
                script_folder, "node_modules", "cldr-localenames-full", "main"
            )
            with open(
                os.path.join(
                    cldr_localenames_path,
                    locale_mapping.get(locale, locale),
                    "languages.json",
                )
            ) as data_file:
                json_data = json.load(data_file)
            cldr_languages = json_data["main"][locale_mapping.get(locale, locale)][
                "localeDisplayNames"
            ]["languages"]

            # Check for different translations
            for locale_code, language in moz_languages.iteritems():
                # IMPORTANT:
                # To reduce the number of differences:
                # - Case is ignored
                # - Mozilla strings are trimmed
                language = language.lower().strip().replace("\u0020", "")
                cldr_language = (
                    cldr_languages[locale_code].lower()
                    if locale_code in cldr_languages
                    else False
                )
                if cldr_language and language != cldr_language:
                    different_values_lang.append(
                        f"{locale_code}\n  CLDR: {cldr_language}\n  Mozilla: {language}"
                    )
            different_values_lang.sort()
            if different_values_lang:
                print("\nDifferent values:")
                print("\n".join(different_values_lang))

        # Read languages from Mozilla repository
        moz_regions = {}
        different_values_reg = []
        l10n_file = os.path.join(
            l10n_path.format(locale),
            "toolkit",
            "chrome",
            "global",
            "regionNames.ftl",
        )
        if os.path.isfile(l10n_file):
            parse_file(l10n_file, moz_regions)

            # Read regions from CLDR
            with open(
                os.path.join(
                    cldr_localenames_path,
                    locale_mapping.get(locale, locale),
                    "territories.json",
                )
            ) as data_file:
                json_data = json.load(data_file)
            cldr_regions = json_data["main"][locale_mapping.get(locale, locale)][
                "localeDisplayNames"
            ]["territories"]

            # Check for different translations
            for region_code, region_name in moz_regions.iteritems():

                code = region_code.upper()
                if code in cldr_regions and region_name != cldr_regions[code]:
                    different_values_reg.append(
                        "{code}\n  CLDR: {cldr_regions[code]}\n  Mozilla: {region_name}"
                    )
            different_values_reg.sort()
            if different_values_reg:
                print("\nDifferent values:")
                print("\n".join(different_values_reg))

        # Append data
        row = [
            f"{locale} ({locale_mapping.get(locale, locale)})",
            len(moz_languages),
            len(different_values_lang),
            round(len(different_values_lang) / float(len(moz_languages)) * 100, 2)
            if len(moz_languages) > 0
            else 0,
            len(moz_regions),
            len(different_values_reg),
            round(len(different_values_reg) / float(len(moz_regions)) * 100, 2)
            if len(moz_regions) > 0
            else 0,
        ]
        csv_rows.append(",".join(map(str, row)))

    # Save .csv data
    with open("output.csv", "w") as f:
        f.write(",Language Names,,,Region Names\n")
        f.write("Locale (CLDR),Total,Differences,%,Total,Differences,%\n")
        csv_rows.sort()
        for line in csv_rows:
            f.write(f"{line}\n")


if __name__ == "__main__":
    main()

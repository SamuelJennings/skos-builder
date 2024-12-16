import os

from babel.support import Translations

TRANSLATION_DIR = os.path.join(os.getcwd(), "locale")


# This is a dummy function that returns the input string as is.
# pybabel extract command will detect any strings wrapped in this function and extract them for translation. actual translations are retrieved using the get_translations_for_string function below.
def gettext(x):
    return x


def get_available_languages():
    """
    Detect available languages with compiled .mo files.

    Args:
        translations_dir (str): Path to the translations directory.

    Returns:
        list: List of available language codes with valid .mo files.
    """
    available_languages = []
    for lang in os.listdir(TRANSLATION_DIR):
        lang_path = os.path.join(TRANSLATION_DIR, lang, "LC_MESSAGES")
        mo_file = os.path.join(lang_path, "messages.mo")
        if os.path.isfile(mo_file):
            available_languages.append(lang)
    return available_languages


def get_translations_for_string(string):
    """
    Get the translated string for a given string across all available languages.

    Args:
        string (str): The translatable string.

    Returns:
        dict: A dictionary with language codes as keys and translated strings as values.
    """
    available_languages = get_available_languages()
    translations_dict = {
        "en": string,
    }

    # Cycle through the available languages and get the translation
    for lang in available_languages:
        translations = Translations.load(TRANSLATION_DIR, [lang])
        translated_string = translations.gettext(string)
        if translated_string != string:
            translations_dict[lang] = translated_string

    return translations_dict

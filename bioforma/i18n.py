"""Two-language UI catalog; scientific inputs and result keys remain invariant."""
from .translations import EN

LANGUAGES = {'pt': 'Português (Brasil)', 'en': 'English'}
_language = 'pt'


def get_language():
    return _language


def set_language(language):
    global _language
    if language not in LANGUAGES:
        raise ValueError('Language must be pt or en.')
    _language = language


def render(message, language):
    return EN.get(message, message) if language == 'en' else message


def tr(message):
    return render(message, _language)


def translate_existing(text, old_language, new_language):
    """Re-label static existing widgets without rebuilding editors or undo history."""
    for message in EN:
        if render(message, old_language) == text:
            return render(message, new_language)
    return text

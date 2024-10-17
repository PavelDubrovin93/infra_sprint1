import re
import inspect

# explicit import to override pytest switch automation
from kittygram_backend import settings as raw_settings


def test_debug():
    assert not raw_settings.DEBUG, (
        'Убедитесь, что для параметра `DEBUG` в файле настроек `settings.py` '
        'бекэнд части проекта `Kittygram` значением является `False`.'
    )


def test_secret_key(settings):
    settings_source = inspect.getsource(raw_settings)
    secret_key = re.sub(r'[\)\(\[\]\$\^\\\*\?\+\|]', '.', settings.SECRET_KEY)
    secret_key_pattern = re.compile(
        r'SECRET_KEY\s*=\s*\(?\s*[\'"]' + secret_key + r'[\'"]\s*\)?'
    )
    assert not re.search(secret_key_pattern, settings_source), (
        'Убедитесь, что для параметра `SECRET_KEY` в настройках бекэнд '
        'части проекта `Kittygram` значение задано с использованием '
        'переменной окружения.'
    )

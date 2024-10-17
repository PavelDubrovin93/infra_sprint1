import base64
import re
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR_NAME = 'backend'
FRONTEND_DIR_NAME = 'frontend'
INFRA_DIR_NAME = 'infra'
DEPLOY_INFO_FILE_NAME = 'kittygram_site.txt'
KITTYGRAM_LINK_KEY = 'name_kittygram'
TASKI_LINK_KEY = 'name_taski'
USERNAME_KEY = 'login'
PASSWORD_KEY = 'password'

for dir_name in (BACKEND_DIR_NAME, FRONTEND_DIR_NAME, INFRA_DIR_NAME):
    path_to_dir = BASE_DIR / dir_name
    if not path_to_dir.is_dir():
        raise AssertionError(
            f'В директории `{BASE_DIR}` не найдена папка проекта '
            f'`{dir_name}/`. Убедитесь, что у вас верная структура проекта.'
        )


@pytest.fixture(scope='session')
def infra_dir_info() -> tuple[Path, str]:
    return (BASE_DIR / INFRA_DIR_NAME, INFRA_DIR_NAME)


@pytest.fixture(scope='session')
def expected_infra_files() -> set[str]:
    return {DEPLOY_INFO_FILE_NAME, 'default', 'gunicorn_kittygram.service'}


@pytest.fixture(scope='session')
def deploy_info_file(infra_dir_info: tuple[Path, str]) -> tuple[Path, str]:
    path, dir_name = infra_dir_info
    deploy_file = path / DEPLOY_INFO_FILE_NAME
    assert deploy_file.is_file(), (
        f'Убедитесь, что в директории `{dir_name}/` создан файл '
        f'`{DEPLOY_INFO_FILE_NAME}`'
    )
    return (deploy_file, f'{dir_name}/{DEPLOY_INFO_FILE_NAME}')


@pytest.fixture(scope='session')
def deploy_info_file_content(
        deploy_info_file: tuple[Path, str]) -> dict[str, str]:
    path, relative_path = deploy_info_file
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        file_content = {}
        line_pattern = re.compile(r'[\w_]+: ?[^;]+;')
        for line_num, line in enumerate(f.readlines(), 1):
            if not line.strip():
                continue
            assert line_pattern.match(line), (
                f'Убедитесь, что строка номер {line_num} файла '
                f'`{relative_path}` соответствует шаблону: '
                '`<ключ>: <значение>;`. В названии ключа '
                'допустимы буквы и нижнее подчеркивание.'
            )
            line = line.strip().strip(';')
            key, value = line.split(':', maxsplit=1)
            file_content[key.strip()] = value.strip()
    return file_content


@pytest.fixture(scope='session')
def expected_deploy_info_file_content() -> dict[str, str]:
    return {
        'IP': 'IP-адрес сервера',
        TASKI_LINK_KEY: 'ссылка для доступа к проекту `Taski`',
        KITTYGRAM_LINK_KEY: 'ссылка для доступа к проекту Kittygram',
        USERNAME_KEY: 'логин',
        PASSWORD_KEY: 'пароль'
    }


@pytest.fixture(params=(TASKI_LINK_KEY, KITTYGRAM_LINK_KEY))
def link_key(request) -> str:
    return request.param


@pytest.fixture(scope='session')
def kittygram_link_key() -> str:
    return KITTYGRAM_LINK_KEY


@pytest.fixture(scope='session')
def taski_link_key() -> str:
    return TASKI_LINK_KEY


@pytest.fixture(scope='session')
def username_key() -> str:
    return USERNAME_KEY


@pytest.fixture(scope='session')
def password_key() -> str:
    return PASSWORD_KEY


@pytest.fixture(scope='session')
def base64_image() -> str:
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    return base64.b64encode(img_io.getvalue()).decode('utf-8')


@pytest.fixture(scope='session')
def kitty_form_data(base64_image: str) -> dict[str, str]:
    return {
        'name': 'Тестовый Барсик',
        'birth_year': '2023',
        'color': '#FFFFFF',
        'image': f'data:image/jpeg;base64,{base64_image}'
    }

import json
import re
from http import HTTPStatus
from pathlib import Path
from typing import Optional

import requests

KITTY_SIGNUP_LINK_PATERN = '{host_url}/api/users/'
KITTY_LOGIN_LINK_PATERN = '{host_url}/api/token/login/'
KITTY_CATS_API_LINK_PATERN = '{host_url}/api/cats/'
IMAGE_URL_KEY = 'image_url'
TOKEN_KEY = 'auth_token'


def _get_validated_link(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        link_key: str
) -> str:
    _, path_to_deploy_info_file = deploy_info_file
    assert link_key in deploy_info_file_content, (
        f'Убедитесь, что файл `{path_to_deploy_info_file}` содержит ключ '
        f'`{link_key}`.'
    )
    link: str = deploy_info_file_content[link_key]
    assert link.startswith('https'), (
        f'Убедитесь, что cсылка ключ `{link_key}` в файле '
        f'`{path_to_deploy_info_file}` содержит ссылку, которая начинается с '
        'префикса `https`.'
    )
    link_pattern = re.compile(
        r'^https:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
        r'[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
    )
    assert link_pattern.match(link), (
        f'Убедитесь, что ключ `{link_key}` в файле '
        f'`{path_to_deploy_info_file}` содержит корректную ссылку.'
    )
    ip_pattern = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    assert not re.search(ip_pattern, link), (
        f'Убедитесь, что значением ключа `{link_key}` в файле '
        f'`{path_to_deploy_info_file}` не является IP-адрес. '
        'Должно использоваться доменное имя.'
    )
    return link.rstrip('/')


def _make_safe_request(link: str, stream: bool = False) -> requests.Response:
    try:
        response = requests.get(link, stream=stream, timeout=15)
    except requests.exceptions.SSLError:
        raise AssertionError(
            f'Убедитесь, что настроили шифрование для `{link}`.'
        )
    except requests.exceptions.ConnectionError:
        raise AssertionError(
            f'Убедитесь, что URL `{link}` доступен.'
        )
    expected_status = HTTPStatus.OK
    assert response.status_code == expected_status, (
        f'Убедитесь, что GET-запрос к `{link}` возвращает ответ со статусом '
        f'{expected_status.value}.'
    )
    return response


def _get_js_link(response: requests.Response) -> Optional[str]:
    js_link_pattern = re.compile(r'static/js/[^\"]+')
    search_result = re.search(js_link_pattern, response.text)
    return search_result.group(0) if search_result else None


def _get_kittygram_auth_api_response(
        host_url: str, signup_link: str, auth_form_data: dict[str, str]
) -> requests.Response:
    try:
        response = requests.post(signup_link, data=auth_form_data, timeout=15)
    except requests.exceptions.SSLError:
        raise AssertionError(
            f'Убедитесь, что настроили шифрование для `{host_url}`.'
        )
    except requests.ConnectionError:
        raise AssertionError(
            'Убедитесь, что API проекта `Kittygram` доступен по ссылке '
            f'формата `{host_url}/api/...`.'
        )
    return response


def _get_json_data_from_response(
        response: requests.Response, link: str) -> dict:
    try:
        return response.json()
    except json.JSONDecodeError:
        raise AssertionError(
            f'Убедитесь, что ответ на запрос к `{link}` содержит данные в '
            'формате JSON.'
        )


def _get_kittygram_auth_header(
        host_url: str, deploy_info_file_content: dict[str, str],
        deploy_info_file: tuple[Path, str], username_key: str,
        password_key: str
) -> dict[str, str]:
    _, path_to_deploy_info_file = deploy_info_file
    loggin_link = KITTY_LOGIN_LINK_PATERN.format(host_url=host_url)
    auth_form_data = {
        'username': deploy_info_file_content[username_key],
        'password': deploy_info_file_content[password_key]
    }
    auth_response = _get_kittygram_auth_api_response(host_url, loggin_link,
                                                     auth_form_data)
    assert auth_response.status_code == HTTPStatus.OK, (
        'На валидный запрос на авторизацию к API проекта `Kittygram` '
        'получен ответ со статус-кодом, отличным от 200. Проверьте '
        'работоспособность проекта и корректность учетных данных, указанных '
        f'в файле {path_to_deploy_info_file}.'
    )
    response_data = _get_json_data_from_response(auth_response, loggin_link)
    assert TOKEN_KEY in response_data, (
        'Не удалось получить токен авторизации API проекта `Kittygram` '
        'через запрос с использованием учетных данных, указанных в файле '
        f'{path_to_deploy_info_file}.'
    )
    return dict(Authorization=f'Token {response_data[TOKEN_KEY]}')


def test_link_connection(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        link_key: str
) -> None:
    link = _get_validated_link(deploy_info_file, deploy_info_file_content,
                               link_key)
    response = _make_safe_request(link)
    cats_project_name = 'Kittygram'
    taski_project_name = 'Taski'
    assert_msg_template = (
        f'Убедитесь, что по ссылке `{link}` доступен проект '
        '`{project_name}`.'
    )
    if link_key == 'name_kittygram':
        assert cats_project_name in response.text, (
            assert_msg_template.format(project_name=cats_project_name)
        )
    else:
        assert_msg = assert_msg_template.format(
            project_name=taski_project_name
        )
        js_link = _get_js_link(response)
        assert js_link, assert_msg
        try:
            taski_response = requests.get(f'{link}/{js_link}')
        except requests.exceptions.ConnectionError:
            raise AssertionError(assert_msg)
        assert taski_response.status_code == HTTPStatus.OK, assert_msg
        assert taski_project_name in taski_response.text, assert_msg


def test_projects_on_same_ip(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        kittygram_link_key: str, taski_link_key: str
) -> None:
    links = [
        _get_validated_link(deploy_info_file, deploy_info_file_content,
                            link_key)
        for link_key in (kittygram_link_key, taski_link_key)
    ]
    responses = [_make_safe_request(link, stream=True) for link in links]
    ips = [
        response.raw._original_response.fp.raw._sock.getpeername()[0]
        for response in responses
    ]
    assert ips[0] == ips[1], (
        'Убедитесь, что оба проекта развернуты на одном сервере. В ходе '
        'проверки обнаружено, что проекты размещены на разных ip-адресах.'
    )


def test_kittygram_static_is_available(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        kittygram_link_key: str
) -> None:
    link = _get_validated_link(deploy_info_file, deploy_info_file_content,
                               kittygram_link_key)
    response = _make_safe_request(link)

    js_link = _get_js_link(response)
    assert js_link, (
        'Проверьте, что проект `Kittygram` настроен корректно. '
        f'В ответе на запрос к `{link}` не обнаружена ссылка на '
        'JavaScript-файл.'
    )
    js_link_response = requests.get(f'{link}/{js_link}')
    assert js_link_response.status_code == HTTPStatus.OK, (
        'Убедитесь, что статические файлы для `Kittygram` доступны.'
    )


def test_kittygram_api_available(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        kittygram_link_key: str
) -> None:
    host_url = _get_validated_link(deploy_info_file, deploy_info_file_content,
                                   kittygram_link_key)
    signup_link = KITTY_SIGNUP_LINK_PATERN.format(host_url=host_url)
    auth_form_data = {
        'username': 'newuser',
        'password': ''
    }
    assert_msg = (
        'Убедитесь, что API проекта `Kittygram` доступен по ссылке формата '
        f'`{host_url}/api/...`.'
    )
    response = _get_kittygram_auth_api_response(host_url, signup_link,
                                                auth_form_data)
    assert response.status_code == HTTPStatus.BAD_REQUEST, assert_msg
    response_data = _get_json_data_from_response(response, signup_link)
    assert 'password' in response_data, assert_msg


def test_kittygram_images_availability(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        kittygram_link_key: str,
        username_key: str,
        password_key: str,
        kitty_form_data: dict[str, str]
):
    host_url = _get_validated_link(deploy_info_file, deploy_info_file_content,
                                   kittygram_link_key)
    cats_link = KITTY_CATS_API_LINK_PATERN.format(host_url=host_url)
    with requests.Session() as session:
        session.headers.update(
            _get_kittygram_auth_header(
                host_url, deploy_info_file_content, deploy_info_file,
                username_key, password_key
            )
        )
        cat_create_response = session.post(cats_link, data=kitty_form_data)
        assert cat_create_response.status_code == HTTPStatus.CREATED, (
            'На валидный запрос на создание кота через API проекта '
            '`Kittygram` получен ответ со статус-кодом, отличным от 201. '
            'Проверьте работоспособность проекта.'
        )
        cat_data = _get_json_data_from_response(cat_create_response, cats_link)
        expected_keys = ('id', IMAGE_URL_KEY)
        for key in expected_keys:
            assert key in cat_data, (
                'В ответе на валидный запрос на создание кота через API '
                f'проекта `Kittygram` отсутствует ключ `{key}`.'
            )
        image_response = session.get(f'{host_url}{cat_data[IMAGE_URL_KEY]}')
        assert image_response.status_code == HTTPStatus.OK, (
            'Проверьте, что в проекте `Kittygram` доступны изображения котов.'
        )
        delete_response = session.delete(f'{cats_link}{cat_data["id"]}')
        assert delete_response.status_code == HTTPStatus.NO_CONTENT, (
            'Проверьте, что в проекте `Kittygram` можно удалить кота.'
        )

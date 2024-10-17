from pathlib import Path


def test_infra_files_exist(infra_dir_info: tuple[Path, str],
                           expected_infra_files: set[str]):
    path, dir_name = infra_dir_info
    infra_dir_content = {obj.name for obj in path.glob('*') if obj.is_file()}
    missing_files = expected_infra_files - infra_dir_content
    action = 'создан файл' if len(missing_files) < 2 else 'созданы файлы'
    assert not missing_files, (
        f'Убедитесь, что в директории `{dir_name}/` {action} '
        f'`{"`, `".join(missing_files)}`.'
    )


def test_deploy_info_file_content(
        deploy_info_file: tuple[Path, str],
        deploy_info_file_content: dict[str, str],
        expected_deploy_info_file_content: dict[str, str]
):
    _, relative_path = deploy_info_file
    missing_content = {
        key: value for key, value in expected_deploy_info_file_content.items()
        if key not in deploy_info_file_content
    }
    action = 'содержится' if len(missing_content) < 2 else 'содержатся'
    key_word_form = 'ключ' if len(missing_content) < 2 else 'ключи'
    assert not missing_content, (
        f'Убедитесь, что в файле `{relative_path}` {action} '
        f'{", ".join(missing_content.values())}. Для вывода этой '
        f'информации необходимо использовать {key_word_form} '
        f'`{"`, `".join(missing_content.keys())}`.'
    )

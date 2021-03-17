import dataclasses
import typing
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML(typ='safe')

ALLOW_MAJOR_UPDATES_NAME = 'allow_major_update'
ALLOW_MINOR_UPDATES_NAME = 'allow_minor_update'
ALLOW_PATCH_UPDATES_NAME = 'allow_patch_update'


@dataclasses.dataclass
class UpdateConfig:
    allow_major_update: bool = False
    allow_minor_update: bool = False
    allow_patch_update: bool = True


@dataclasses.dataclass
class Version:
    major: int = 0
    minor: int = 0
    patch: int = 0


def update_injection_library(root_dir: Path):
    """Controller"""
    release_to_install = get_release_to_install(root_dir)
    current_release = _get_current_release(root_dir)
    if current_release != release_to_install:
        install_release(root_dir, release_to_install)


def get_release_to_install(root_dir: Path) -> Version:
    """Controller"""
    update_config = _get_update_config(root_dir)
    releases = _get_releases()
    release_to_install = _get_release_to_install_from_config_and_releases(
        update_config, releases)
    return release_to_install


def _get_update_config(root_dir: Path) -> UpdateConfig:
    """Controller"""
    config_text = _read_config(root_dir)
    update_config = _make_update_config(config_text)
    raise NotImplementedError


def _read_config(root_dir: Path) -> str:
    """Controller"""
    raise NotImplementedError


def _make_update_config(config_text: str) -> UpdateConfig:
    config_yaml: typing.Optional[dict] = yaml.load(config_text)
    if not config_yaml:
        return UpdateConfig()
    return UpdateConfig(
        allow_major_update=config_yaml.get('allow_major_update', False),
        allow_minor_update=config_yaml.get('allow_minor_update', False),
        allow_patch_update=config_yaml.get('allow_patch_update', True))


def _get_releases() -> list[Version]:
    """Controller"""
    raise NotImplementedError


def _get_release_to_install_from_config_and_releases(
        update_config: UpdateConfig, releases: list[Version]) -> Version:
    raise NotImplementedError


def _get_current_release(root_dir: Path) -> Version:
    """Controller"""
    dotfile = read_dotfile(root_dir)
    return _get_current_release_from_dotfile(dotfile)


def _get_current_release_from_dotfile(dotfile: str) -> Version:
    raise NotImplementedError


def install_release(root_dir: Path, release: Version):
    """Controller"""
    _delete_old_release(root_dir)
    _download_and_unzip_release(root_dir)
    _update_dotfile_with_new_release(root_dir, release)


def _delete_old_release(root_dir: Path):
    """Controller"""
    raise NotImplementedError


def _download_and_unzip_release(root_dir: Path):
    """Controller"""
    raise NotImplementedError


def _update_dotfile_with_new_release(root_dir: Path, release: Version):
    """Controller"""
    old_dotfile = read_dotfile(root_dir)
    new_dotfile = _get_dotfile_with_new_release(release, old_dotfile)
    save_dotfile(root_dir, new_dotfile)


def read_dotfile(root_dir: Path):
    """Controller"""
    raise NotImplementedError


def _get_dotfile_with_new_release(
        release: Version, old_dotfile: str) -> str:
    raise NotImplementedError


def save_dotfile(root_dir: Path, dotfile: str):
    """Controller"""
    raise NotImplementedError

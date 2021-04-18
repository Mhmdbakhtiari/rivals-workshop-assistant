import datetime
from pathlib import Path

import pytest
from testfixtures import TempDirectory

from rivals_workshop_assistant.dotfile_mod import VERSION, LAST_UPDATED
import rivals_workshop_assistant.injection.paths as inject_paths
import rivals_workshop_assistant.paths as paths
from rivals_workshop_assistant.injection import installation as src
from tests.testing_helpers import (
    create_script,
    ScriptWithPath,
    make_release,
    make_version,
    test_date_string,
    assert_script_with_path,
)

pytestmark = pytest.mark.slow


def test__get_update_config():
    with TempDirectory() as tmp:
        create_script(
            tmp,
            ScriptWithPath(
                path=paths.ASSISTANT_CONFIG_PATH,
                content=f"""\

{src.UPDATE_LEVEL_NAME}: minor

""",
            ),
        )

        result = src.get_update_config(Path(tmp.path))
        assert result == src.UpdateConfig.MINOR


def test__get_releases():
    result = src.get_releases()

    assert len(result) > 0 and isinstance(result[0], src.Release)
    # Not going to mock it out, just make sure we get
    #   something


def test__update_dotfile_with_new_release():
    with TempDirectory() as tmp:
        create_script(
            tmp, ScriptWithPath(path=paths.DOTFILE_PATH, content="other_content: 42")
        )

        src._update_dotfile_for_install(
            root_dir=Path(tmp.path),
            version=make_version("4.5.6"),
            last_updated=datetime.date.fromisoformat(test_date_string),
        )

        result = tmp.read(paths.DOTFILE_PATH.as_posix(), encoding="utf8")
        assert (
            result
            == f"""\
other_content: 42
{VERSION}: 4.5.6
{LAST_UPDATED}: {test_date_string}
"""
        )


def test__update_dotfile_with_new_release_when_missing_dotfile():
    with TempDirectory() as tmp:
        src._update_dotfile_for_install(
            root_dir=Path(tmp.path),
            version=src.Version(major=4, minor=5, patch=6),
            last_updated=datetime.date.fromisoformat("2019-12-04"),
        )
        result = tmp.read(paths.DOTFILE_PATH.as_posix(), encoding="utf8")

        assert (
            result
            == f"""\
{VERSION}: 4.5.6
{LAST_UPDATED}: {test_date_string}
"""
        )


TEST_RELEASE = make_release(
    "0.0.0",
    "https://github.com/Rivals-Workshop-Community-Projects"
    "/injector-library/archive/0.0.0.zip",
)


def test__delete_old_release():
    with TempDirectory() as tmp:
        create_script(
            tmp,
            ScriptWithPath(
                path=inject_paths.INJECT_FOLDER / "test.gml", content="test content"
            ),
        )

        src._delete_old_release(Path(tmp.path))

        tmp.compare(path=inject_paths.INJECT_FOLDER.as_posix(), expected=())


def test__delete_old_release__none_exists():
    with TempDirectory() as tmp:
        src._delete_old_release(Path(tmp.path))

        tmp.compare(path=inject_paths.INJECT_FOLDER.as_posix(), expected=())


def assert_test_release_scripts_installed(tmp):
    file_contents = tmp.read(
        (inject_paths.INJECT_FOLDER / "logging.gml").as_posix(), encoding="utf8"
    )
    assert (
        file_contents
        == """\
#define prints()
    // Prints each parameter to console, separated by spaces.
    var _out_string = argument[0]
    for var i = 1; i < argument_count; i++ {
        _out_string += " "
        _out_string += string(argument[i])
    }
    print(_out_string)"""
    )


def test__download_and_unzip_release():
    with TempDirectory() as tmp:
        src._download_and_unzip_release(root_dir=Path(tmp.path), release=TEST_RELEASE)
        assert_test_release_scripts_installed(tmp)


def test__update_dotfile__no_dotfile():
    with TempDirectory() as tmp:
        src._update_dotfile_for_install(
            root_dir=Path(tmp.path),
            version=make_version("4.5.6"),
            last_updated=datetime.date.fromisoformat("2019-12-04"),
        )

        dotpath_content = tmp.read(
            filepath=paths.DOTFILE_PATH.as_posix(), encoding="utf8"
        )
        assert (
            dotpath_content
            == f"""\
{VERSION}: 4.5.6
{LAST_UPDATED}: {test_date_string}
"""
        )


def test__update_dotfile():
    with TempDirectory() as tmp:
        create_script(
            tmp,
            ScriptWithPath(
                path=paths.DOTFILE_PATH,
                content=f"{VERSION}: 3.4.5\n",
            ),
        )
        src._update_dotfile_for_install(
            root_dir=Path(tmp.path),
            version=make_version("4.5.6"),
            last_updated=datetime.date.fromisoformat("2019-12-04"),
        )

        dotfile = tmp.read(filepath=paths.DOTFILE_PATH.as_posix(), encoding="utf8")
        assert (
            dotfile
            == f"""\
{VERSION}: 4.5.6
{LAST_UPDATED}: {test_date_string}
"""
        )


def test__install_release():
    with TempDirectory() as tmp:
        create_script(
            tmp,
            ScriptWithPath(
                path=paths.DOTFILE_PATH,
                content=f"{VERSION}: 0.0.0",
            ),
        )
        create_script(
            tmp,
            ScriptWithPath(
                path=paths.ASSISTANT_CONFIG_PATH, content="update_level: none"
            ),
        )
        create_script(
            tmp,
            ScriptWithPath(
                path=inject_paths.INJECT_FOLDER / "test.gml", content="test content"
            ),
        )
        existing_user_inject = ScriptWithPath(
            path=inject_paths.USER_INJECT_FOLDER / "users.gml", content="whatever"
        )
        create_script(tmp, existing_user_inject)

        src.install_release(root_dir=Path(tmp.path), release=TEST_RELEASE)
        assert_test_release_scripts_installed(tmp)
        assert_script_with_path(tmp, existing_user_inject)

from rivals_workshop_assistant.injection import installation as src


def test__make_update_config_empty():
    config_text = ""

    result = src._make_update_config(config_text)
    assert result == src.UpdateConfig(allow_major_update=False,
                                      allow_minor_update=False,
                                      allow_patch_update=True)


def test__make_update_config_allow_major():
    config_text = f"""\
{src.ALLOW_MAJOR_UPDATES_NAME}: true"""

    result = src._make_update_config(config_text)
    assert result == src.UpdateConfig(allow_major_update=True,
                                      allow_minor_update=False,
                                      allow_patch_update=True)


def test__make_update_config_disallow_major():
    config_text = f"""\
{src.ALLOW_MAJOR_UPDATES_NAME}: false"""

    result = src._make_update_config(config_text)
    assert result == src.UpdateConfig(allow_major_update=False,
                                      allow_minor_update=False,
                                      allow_patch_update=True)


def test__make_update_config_allow_minor_and_major():
    config_text = f"""\
{src.ALLOW_MAJOR_UPDATES_NAME}: true
{src.ALLOW_MINOR_UPDATES_NAME}: true"""

    result = src._make_update_config(config_text)
    assert result == src.UpdateConfig(allow_major_update=True,
                                      allow_minor_update=True,
                                      allow_patch_update=True)


def test__make_update_config_disallow_patch():
    config_text = f"""\
{src.ALLOW_PATCH_UPDATES_NAME}: false"""

    result = src._make_update_config(config_text)
    assert result == src.UpdateConfig(allow_major_update=False,
                                      allow_minor_update=False,
                                      allow_patch_update=False)


def test__get_current_release_from_empty_dotfile():
    dotfile = ""
    result = src.get_current_release_from_dotfile(dotfile)
    assert result is None


def test__get_current_release_from_dotfile():
    dotfile = "version: 3.2.1"
    result = src.get_current_release_from_dotfile(dotfile)
    assert result == src.Version(major=3, minor=2, patch=1)


def test__get_dotfile_with_new_release():
    release = src.Version(major=10, minor=11, patch=12)
    old_dotfile = "version: 3.2.1"

    result = src._get_dotfile_with_new_release(release=release,
                                               old_dotfile=old_dotfile)
    assert result == "version: 10.11.12\n"


def test__get_dotfile_with_new_release_with_other_data():
    release = src.Version(major=10, minor=11, patch=12)
    old_dotfile = """\
something_else: version
version: 3.2.1"""

    result = src._get_dotfile_with_new_release(release=release,
                                               old_dotfile=old_dotfile)
    assert result == """\
something_else: version
version: 10.11.12
"""




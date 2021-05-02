import datetime
import sys
from pathlib import Path

from rivals_workshop_assistant import (
    updating,
    assistant_config_mod,
    dotfile_mod,
    character_config_mod,
)
from rivals_workshop_assistant.assistant_config_mod import get_has_small_sprites
from rivals_workshop_assistant.dotfile_mod import update_dotfile_after_saving
from rivals_workshop_assistant.script_mod import read_scripts
from rivals_workshop_assistant.aseprite_handling import (
    get_aseprite_path,
    read_aseprites,
    get_anims,
    save_scripts,
    save_aseprites,
)
from rivals_workshop_assistant.asset_handling import get_required_assets, save_assets
from rivals_workshop_assistant.setup import make_basic_folder_structure
from rivals_workshop_assistant.injection import handle_injection
from rivals_workshop_assistant.code_generation import handle_codegen


def main(given_dir: Path, guarantee_root_dir: bool = False):
    """Runs all processes on scripts in the root_dir"""
    if guarantee_root_dir:
        root_dir = given_dir
    else:
        root_dir = get_root_dir(given_dir)
    make_basic_folder_structure(root_dir)
    dotfile = dotfile_mod.read(root_dir)
    assistant_config = assistant_config_mod.read(root_dir)
    character_config = character_config_mod.read(root_dir)

    updating.update(root_dir=root_dir, dotfile=dotfile, config=assistant_config)

    scripts = read_scripts(root_dir, dotfile)
    aseprites = read_aseprites(
        root_dir, dotfile=dotfile, assistant_config=assistant_config
    )

    scripts = handle_codegen(scripts)
    scripts = handle_injection(
        root_dir=root_dir, scripts=scripts, anims=get_anims(aseprites)
    )

    save_scripts(root_dir, scripts)

    save_aseprites(
        root_dir,
        aseprite_path=get_aseprite_path(assistant_config),
        aseprites=aseprites,
        has_small_sprites=get_has_small_sprites(
            scripts=scripts, character_config=character_config
        ),
    )
    update_dotfile_after_saving(
        now=datetime.datetime.now(), dotfile=dotfile, files=scripts + aseprites
    )

    assets = get_required_assets(scripts)
    save_assets(root_dir, assets)

    dotfile_mod.save_dotfile(root_dir, dotfile)


def get_root_dir(given_dir: Path) -> Path:
    """Return the absolute path to the character's root directory, containing
    their config file.
    Currently assumes that that path is passed as the first argument"""
    if "config.ini" in [path.name for path in given_dir.glob("*")]:
        return given_dir
    else:
        file_names = "\n".join([path.name for path in given_dir.glob("*")])
        raise FileNotFoundError(
            f"""Given folder does not contain config.ini.
Current directory is: {given_dir}
Files in current directory are: {file_names}"""
        )


if __name__ == "__main__":
    root_dir = Path(sys.argv[1])
    main(root_dir)

import itertools
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

from rivals_workshop_assistant import paths, assistant_config_mod
from ._aseprite_loading import RawAsepriteFile
from .constants import (
    ANIMS_WHICH_CARE_ABOUT_SMALL_SPRITES,
    HURTMASK_LAYER_NAME,
    HURTBOX_LAYER_NAME,
    ANIMS_WHICH_GET_HURTBOXES,
)
from ..file_handling import File, _get_modified_time
from ..dotfile_mod import get_processed_time
from .types import AsepriteTag, TagColor
from ..paths import ASEPRITE_LUA_SCRIPTS_PATH
from ..script_mod import Script


class TagObject:
    def __init__(self, name: str, start: int, end: int):
        self.name = name
        self.start = start
        self.end = end


class Window(TagObject):
    """An attack window in an anim.
    Start and end are relative to the anim, not the aseprite file."""

    def __init__(self, name: str, start: int, end: int):
        super().__init__(name, start, end)
        self.gml = self._make_gml()

    def _make_gml(self):
        return f"""\
#macro {self.name.upper()}_FRAMES {self.end - self.start + 1}
#macro {self.name.upper()}_FRAME_START {self.start}"""


class Anim(TagObject):
    def __init__(
        self,
        name: str,
        start: int,
        end: int,
        windows: List[Window] = None,
        is_fresh=False,
    ):
        """A part of an aseprite file representing a single spritesheet.
        An Aseprite file may contain multiple anims.
        """
        super().__init__(name, start, end)
        if windows is None:
            windows = []
        self.windows = windows
        self.is_fresh = is_fresh

    @property
    def num_frames(self):
        return self.end - self.start + 1

    def __eq__(self, other):
        return self.name == other.name

    def save(
        self,
        root_dir: Path,
        aseprite_path: Path,
        aseprite_file_path: Path,
        has_small_sprites: bool,
        hurtboxes_enabled: bool,
    ):
        root_name = get_anim_file_name_root(root_dir, aseprite_file_path, self.name)
        if has_small_sprites and self._cares_about_small_sprites():
            scale_param = 1
        else:
            scale_param = 2
        self._run_lua_export(
            root_dir=root_dir,
            aseprite_file_path=aseprite_file_path,
            aseprite_path=aseprite_path,
            base_name=root_name,
            script_name="export_aseprite.lua",
            lua_params={"scale": scale_param},
        )

        if hurtboxes_enabled and self._gets_a_hurtbox():
            self._run_lua_export(
                root_dir=root_dir,
                aseprite_file_path=aseprite_file_path,
                aseprite_path=aseprite_path,
                base_name=f"{root_name}_hurt",
                script_name="create_hurtbox.lua",
            )

    def _run_lua_export(
        self,
        root_dir: Path,
        aseprite_file_path: Path,
        aseprite_path: Path,
        base_name: str,
        script_name: str,
        lua_params: dict = None,
    ):
        if lua_params is None:
            lua_params = {}

        _delete_paths_from_glob(
            root_dir,
            f"{base_name}" + "_strip*.png",
        )

        dest_name = f"{base_name}" + f"_strip{self.num_frames}.png"
        dest = root_dir / paths.SPRITES_FOLDER / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)

        command_parts = (
            [
                f'"{aseprite_path}"',
                "-b",
                f"-script-param filename={aseprite_file_path}",
                f"-script-param dest={dest}",
                f"-script-param startFrame={self.start + 1}",
                f"-script-param endFrame={self.end + 1}",
            ]
            + [f"-script-param {key}={value}" for key, value in lua_params.items()]
            + [
                f"-script {ASEPRITE_LUA_SCRIPTS_PATH / script_name}",
            ]
        )
        export_command = " ".join(command_parts)
        subprocess.run(export_command)

    def _cares_about_small_sprites(self):
        return self.name in ANIMS_WHICH_CARE_ABOUT_SMALL_SPRITES

    def _gets_a_hurtbox(self):
        return self.name in ANIMS_WHICH_GET_HURTBOXES


def _delete_paths_from_glob(root_dir: Path, paths_glob: str):
    """Delete paths matching the glob"""
    old_paths = (root_dir / paths.SPRITES_FOLDER).glob(paths_glob)
    for old_path in old_paths:
        os.remove(old_path)


def get_anim_file_name_root(root_dir: Path, aseprite_file_path: Path, name: str) -> str:
    """Return the anim's name, prefixed with any subfolders the anim is in.
    anims/vfx/hitfx/star.aseprite -> 'vfx_hitfx_star'"""
    try:
        relative_path = aseprite_file_path.relative_to(root_dir / paths.ANIMS_FOLDER)
    except ValueError:
        # The aseprite file path isn't in the root dir, maybe because testing.
        return name
    subfolders = list(relative_path.parents)[:-1]
    path_parts = [path.name for path in reversed(subfolders)] + [name]
    base_name = "_".join(path_parts)
    return base_name


class AsepriteData:
    def __init__(
        self,
        name: str,
        num_frames: int,
        anim_tag_color: TagColor,
        window_tag_color: TagColor,
        tags: List[AsepriteTag] = None,
        is_fresh: bool = False,
    ):
        self.num_frames = num_frames
        if tags is None:
            tags = []
        self.tags = tags
        self.anim_tag_color = anim_tag_color
        self.window_tag_color = window_tag_color
        self.is_fresh = is_fresh

        self.anims = self.get_anims(name)

    @classmethod
    def from_path(
        cls,
        name: str,
        path: Path,
        anim_tag_color: TagColor,
        window_tag_color: TagColor,
        is_fresh: bool,
    ):
        with open(path, "rb") as f:
            contents = f.read()
            raw_aseprite_file = RawAsepriteFile(contents)
        tags = raw_aseprite_file.get_tags()
        num_frames = raw_aseprite_file.get_num_frames()
        return cls(
            name=name,
            tags=tags,
            num_frames=num_frames,
            anim_tag_color=anim_tag_color,
            window_tag_color=window_tag_color,
            is_fresh=is_fresh,
        )

    def get_anims(self, name: str):
        tag_anims = [
            self.make_anim(
                name=tag.name, start=tag.start, end=tag.end, is_fresh=self.is_fresh
            )
            for tag in self.tags
            if tag.color == self.anim_tag_color
        ]
        if tag_anims:
            return tag_anims
        else:
            return [
                self.make_anim(
                    name=name, start=0, end=self.num_frames - 1, is_fresh=self.is_fresh
                )
            ]

    def make_anim(self, name: str, start: int, end: int, is_fresh: bool):
        return Anim(
            name=name,
            start=start,
            end=end,
            windows=self.get_windows_in_frame_range(start=start, end=end),
            is_fresh=is_fresh,
        )

    def get_windows_in_frame_range(self, start: int, end: int):
        tags_in_frame_range = [
            window
            for window in self.tags
            if window.color == self.window_tag_color
            and start <= window.start <= end
            and start <= window.end <= end
        ]
        windows = [
            Window(name=tag.name, start=tag.start - start + 1, end=tag.end - start + 1)
            for tag in tags_in_frame_range
        ]
        return windows


class Aseprite(File):
    def __init__(
        self,
        path: Path,
        anim_tag_color: TagColor,
        window_tag_color: TagColor,
        modified_time: datetime = None,
        processed_time: datetime = None,
        content=None,
    ):
        super().__init__(path, modified_time, processed_time)
        self.anim_tag_color = anim_tag_color
        self.window_tag_color = window_tag_color
        self._content = content

    @property
    def content(self) -> AsepriteData:
        if self._content is None:
            self._content = AsepriteData.from_path(
                name=self.path.stem,
                path=self.path,
                anim_tag_color=self.anim_tag_color,
                window_tag_color=self.window_tag_color,
                is_fresh=self.is_fresh,
            )
        return self._content

    @property
    def name(self):
        return self.path.stem

    def save(
        self,
        root_dir: Path,
        aseprite_path: Path,
        has_small_sprites: bool = False,
        hurtboxes_enabled=False,
    ):
        for anim in self.content.anims:
            anim.save(
                root_dir=root_dir,
                aseprite_path=aseprite_path,
                aseprite_file_path=self.path,
                has_small_sprites=has_small_sprites,
                hurtboxes_enabled=hurtboxes_enabled,
            )


def read_aseprites(
    root_dir: Path, dotfile: dict, assistant_config: dict
) -> List[Aseprite]:
    ase_paths = itertools.chain(
        *[
            list((root_dir / "anims").rglob(f"*.{filetype}"))
            for filetype in ("ase", "aseprite")
        ]
    )

    aseprites = []
    for path in ase_paths:
        aseprite = read_aseprite(path, dotfile, assistant_config)
        aseprites.append(aseprite)
    return aseprites


def read_aseprite(path: Path, dotfile: dict, assistant_config: dict):
    aseprite = Aseprite(
        path=path,
        modified_time=_get_modified_time(path),
        processed_time=get_processed_time(dotfile=dotfile, path=path),
        anim_tag_color=assistant_config_mod.get_anim_tag_color(assistant_config),
        window_tag_color=assistant_config_mod.get_window_tag_color(assistant_config),
    )
    return aseprite


def get_anims(aseprites: List[Aseprite]) -> List[Anim]:
    return list(itertools.chain(*[aseprite.content.anims for aseprite in aseprites]))
    # Unfortunately this involves reading every aseprite file...
    # If we demand that multi-anim files have a name prefix,
    # we could get away with reading fewer files.


def save_scripts(root_dir: Path, scripts: List[Script]):
    # Why is this in aseprite_handling? Move?
    for script in scripts:
        script.save(root_dir)


def save_anims(
    root_dir: Path,
    aseprite_path: Path,
    aseprites: List[Aseprite],
    has_small_sprites: bool,
    hurtboxes_enabled: bool = False,
):
    if not aseprite_path:
        return
    for aseprite in aseprites:
        if aseprite.is_fresh:
            aseprite.save(
                root_dir=root_dir,
                aseprite_path=aseprite_path,
                has_small_sprites=has_small_sprites,
                hurtboxes_enabled=hurtboxes_enabled,
            )

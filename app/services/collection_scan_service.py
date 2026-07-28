"""Filesystem scanning of a Collection's data_location for tilt-series thumbnails.

Tilt-series data is not persisted to the database; it is derived on each request by
walking the directory a Collection points at, which is expected to look like:

    <data_location>/
      <tilt_series_name>/
        <tilt_series_name>_Align.jpg
        motion/
          <tilt_series_name>_<idx>_<angle>.mc.jpg   (one frame per tilt angle)
        tomogram/
          <tilt_series_name>_tomogram.jpg
          <tilt_series_name>_tomogram_projXY.jpg
          <tilt_series_name>_tomogram_projXZ.jpg
"""
import os
import re
from dataclasses import dataclass

MOTION_FRAME_RE = re.compile(r"^.+_(?P<idx>\d{3})_(?P<angle>-?\d+(?:\.\d+)?)\.mc\.jpg$", re.IGNORECASE)


@dataclass
class TiltSeriesInfo:
    name: str
    align_image: str | None
    tomogram_image: str | None
    tomogram_projxy_image: str | None
    tomogram_projxz_image: str | None
    tilt_count: int
    min_angle: float | None
    max_angle: float | None
    mtime: float


def _scan_one(data_location: str, name: str) -> TiltSeriesInfo | None:
    folder = os.path.join(data_location, name)
    motion_dir = os.path.join(folder, "motion")
    tomogram_dir = os.path.join(folder, "tomogram")
    has_motion = os.path.isdir(motion_dir)
    has_tomogram = os.path.isdir(tomogram_dir)
    if not (has_motion or has_tomogram):
        return None

    mtime = os.path.getmtime(folder)

    align_image = None
    align_candidate = os.path.join(folder, f"{name}_Align.jpg")
    if os.path.isfile(align_candidate):
        align_image = f"{name}/{name}_Align.jpg"
        mtime = max(mtime, os.path.getmtime(align_candidate))

    tomogram_image = None
    tomogram_projxy_image = None
    tomogram_projxz_image = None
    if has_tomogram:
        for suffix, attr in (
            ("_tomogram.jpg", "tomogram_image"),
            ("_tomogram_projXY.jpg", "tomogram_projxy_image"),
            ("_tomogram_projXZ.jpg", "tomogram_projxz_image"),
        ):
            candidate = os.path.join(tomogram_dir, f"{name}{suffix}")
            if os.path.isfile(candidate):
                relative = f"{name}/tomogram/{name}{suffix}"
                mtime = max(mtime, os.path.getmtime(candidate))
                if attr == "tomogram_image":
                    tomogram_image = relative
                elif attr == "tomogram_projxy_image":
                    tomogram_projxy_image = relative
                else:
                    tomogram_projxz_image = relative

    tilt_count = 0
    min_angle = None
    max_angle = None
    if has_motion:
        angles = []
        for filename in os.listdir(motion_dir):
            match = MOTION_FRAME_RE.match(filename)
            if match:
                angles.append(float(match.group("angle")))
        tilt_count = len(angles)
        if angles:
            min_angle = min(angles)
            max_angle = max(angles)
        motion_mtime = os.path.getmtime(motion_dir)
        mtime = max(mtime, motion_mtime)

    return TiltSeriesInfo(
        name=name,
        align_image=align_image,
        tomogram_image=tomogram_image,
        tomogram_projxy_image=tomogram_projxy_image,
        tomogram_projxz_image=tomogram_projxz_image,
        tilt_count=tilt_count,
        min_angle=min_angle,
        max_angle=max_angle,
        mtime=mtime,
    )


def scan_tilt_series(data_location: str) -> list[TiltSeriesInfo]:
    """Return one TiltSeriesInfo per immediate subdirectory of data_location that
    looks like a tilt-series folder (i.e. contains a motion/ or tomogram/ subdir).
    """
    if not data_location or not os.path.isdir(data_location):
        return []

    results = []
    for entry in sorted(os.listdir(data_location)):
        full_path = os.path.join(data_location, entry)
        if not os.path.isdir(full_path):
            continue
        info = _scan_one(data_location, entry)
        if info is not None:
            results.append(info)
    return results


def resolve_safe_path(data_location: str, relative_path: str) -> str | None:
    """Resolve relative_path against data_location, guarding against path traversal.

    Returns the resolved absolute path, or None if it would escape data_location.
    """
    base_dir = os.path.realpath(data_location)
    requested = os.path.realpath(os.path.join(base_dir, relative_path))
    if requested != base_dir and not requested.startswith(base_dir + os.sep):
        return None
    return requested

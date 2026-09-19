"""จุดเดียวในโปรเจกต์ที่รู้ว่าไฟล์อยู่ตรงไหน

เหตุผลที่ต้องมีไฟล์นี้: โค้ดต้องรันได้ทั้งบนโน้ตบุ๊ก Windows และบน Raspberry Pi
ถ้าปล่อยให้แต่ละสคริปต์เขียน path เองจะมี ``D:\\ACER\\...`` โผล่กระจายเต็มไปหมด
พอย้ายไป Pi ก็พังทั้งยวง โมดูลอื่นจึงต้องเรียกฟังก์ชันในไฟล์นี้เท่านั้น
ห้ามประกอบ path เอง

ลำดับความสำคัญในการหาโฟลเดอร์ data:
    1. environment variable ``EDGE_PDM_DATA``    ชี้ตรงไปที่โฟลเดอร์ data
    2. environment variable ``EDGE_PDM_PROFILE`` เลือก profile ใน config.yaml
    3. ``active_profile`` ใน config.yaml

ตัวอย่างการใช้บน Pi ที่อยากเก็บ data ไว้บน USB drive แทน microSD::

    EDGE_PDM_DATA=/mnt/usb/edge-pdm-data python src/data/verify_dataset.py
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_FILENAME = "config.yaml"


@lru_cache(maxsize=1)
def repo_root() -> Path:
    """ไต่ขึ้นจากตำแหน่งไฟล์นี้จนเจอโฟลเดอร์ที่มี config.yaml

    ใช้ ``__file__`` เป็นจุดตั้งต้นแทน ``Path.cwd()`` โดยตั้งใจ เพราะ cwd
    เปลี่ยนไปตามที่ผู้ใช้เรียกสคริปต์ แต่ตำแหน่งไฟล์ไม่เปลี่ยน
    ทำให้ ``python src/data/verify_dataset.py`` กับ ``python verify_dataset.py``
    จาก notebook ให้ผลเหมือนกัน
    """
    for candidate in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (candidate / CONFIG_FILENAME).is_file():
            return candidate
    raise FileNotFoundError(
        f"หา {CONFIG_FILENAME} ไม่เจอ เมื่อไต่ขึ้นจาก {Path(__file__).resolve()} "
        "— รันจากในโปรเจกต์ edge-pdm อยู่หรือเปล่า"
    )


@lru_cache(maxsize=1)
def load_config() -> dict:
    """อ่าน config.yaml ทั้งก้อน (cache ไว้ อ่านดิสก์ครั้งเดียวต่อโปรเซส)"""
    with open(repo_root() / CONFIG_FILENAME, encoding="utf-8") as f:
        return yaml.safe_load(f)


def active_profile_name() -> str:
    """ชื่อ profile ที่ใช้อยู่ — env EDGE_PDM_PROFILE ทับค่าในไฟล์ได้"""
    return os.environ.get("EDGE_PDM_PROFILE") or load_config()["active_profile"]


def profile() -> dict:
    """ก้อน config ของ profile ที่ใช้อยู่"""
    name = active_profile_name()
    profiles = load_config()["profiles"]
    if name not in profiles:
        raise KeyError(
            f"ไม่รู้จัก profile {name!r} — ที่มีให้เลือกคือ {sorted(profiles)}"
        )
    return profiles[name]


def data_dir() -> Path:
    """โฟลเดอร์ data ระดับบนสุด คืนค่าเป็น path สัมบูรณ์เสมอ"""
    override = os.environ.get("EDGE_PDM_DATA")
    if override:
        return Path(override).expanduser().resolve()
    return (repo_root() / profile()["data_root"]).resolve()


def raw_dir() -> Path:
    """ข้อมูลดิบ — อ่านอย่างเดียว ห้ามเขียนทับเด็ดขาด"""
    return data_dir() / "raw"


def interim_dir() -> Path:
    """ผลระหว่างทาง เช่น สัญญาณที่กรองแล้ว"""
    return data_dir() / "interim"


def processed_dir() -> Path:
    """feature ที่สกัดแล้ว พร้อมเทรน"""
    return data_dir() / "processed"


def mafaulda_dir() -> Path:
    """รากของ dataset MAFAULDA"""
    return data_dir() / load_config()["dataset"]["mafaulda"]["subdir"]


def ensure_output_dirs() -> None:
    """สร้างโฟลเดอร์ปลายทางที่เขียนได้ ถ้ายังไม่มี

    จงใจไม่สร้าง ``raw_dir()`` เพราะข้อมูลดิบต้องมาจากการแตก archive เท่านั้น
    ถ้าโค้ดสร้างโฟลเดอร์ raw ให้เองได้ วันหนึ่งจะมีสคริปต์เผลอเขียนทับลงไป
    """
    for d in (interim_dir(), processed_dir()):
        d.mkdir(parents=True, exist_ok=True)


def mafaulda_columns() -> list[str]:
    """ชื่อคอลัมน์ทั้ง 8 ตามลำดับใน CSV (ซึ่งไม่มี header)"""
    return list(load_config()["dataset"]["mafaulda"]["columns"])


def sampling_rate() -> int:
    """อัตราสุ่มของ MAFAULDA (Hz)"""
    return int(load_config()["dataset"]["mafaulda"]["fs"])


def bearing_coefficients() -> dict[str, float]:
    """ตัวคูณความถี่ความเสียหาย คูณกับความถี่หมุน (Hz) ได้เลย"""
    return dict(load_config()["bearing"]["coefficients"])


if __name__ == "__main__":
    print(f"profile     : {active_profile_name()}")
    print(f"repo_root   : {repo_root()}")
    print(f"data_dir    : {data_dir()}")
    print(f"mafaulda_dir: {mafaulda_dir()}  (exists={mafaulda_dir().exists()})")

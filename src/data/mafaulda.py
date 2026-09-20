"""ทำดัชนีและโหลดไฟล์ MAFAULDA

ทำไมต้องมีดัชนี: dataset มี 1,951 ไฟล์กระจายอยู่ในโครงสร้างโฟลเดอร์ 3 ชั้น
ที่ไม่เหมือนกันในแต่ละคลาส (normal ไม่มีชั้นย่อย, imbalance มีชั้นมวล,
bearing fault มีทั้งชั้นชนิดความเสียหายและชั้นมวล) ถ้าปล่อยให้แต่ละสคริปต์
ไล่ glob เองจะเขียนผิดกันคนละแบบ โมดูลนี้แปลงทั้งหมดเป็นตารางเดียว

คอลัมน์ในตารางดัชนี
    path        Path เต็มของไฟล์
    rel         path เทียบกับรากของ dataset (ไว้แสดงผล)
    cls         คลาสหลัก 6 คลาส
    subclass    ชนิดความเสียหายหรือระดับความรุนแรง เช่น outer_race, 1.0mm, 20g
    mass_g      มวลถ่วงที่เติมเข้าไป (g) — 0 เมื่อไม่มี
    severity    ระยะเยื้องศูนย์ (mm) สำหรับ misalignment — NaN เมื่อไม่เกี่ยว
    rot_hz      ความถี่การหมุนจากชื่อไฟล์ (Hz) = ground truth
    rot_rpm     rot_hz * 60

**หมายเหตุสำคัญ** `rot_hz` มาจากชื่อไฟล์ ไม่ได้คำนวณจากสัญญาณ tachometer
ใช้ได้สำหรับการสำรวจข้อมูล แต่ตอนทำ Checkpoint 2 ขั้นที่ 1 ต้องคำนวณจาก
tachometer จริงแล้วเอามาเทียบกับคอลัมน์นี้ เพื่อตรวจว่าโค้ดถูก
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import interim_dir, mafaulda_columns, mafaulda_dir  # noqa: E402

INDEX_CACHE = "mafaulda_index.csv"

# ชื่อคลาสแบบสั้นไว้ใช้บนกราฟ ชื่อโฟลเดอร์ยาวเกินไปสำหรับหัวแผง
CLASS_LABELS = {
    "normal": "Normal",
    "imbalance": "Imbalance",
    "horizontal-misalignment": "Horiz. misalign",
    "vertical-misalignment": "Vert. misalign",
    "underhang": "Underhang bearing",
    "overhang": "Overhang bearing",
}

# ลำดับที่ใช้ทุกที่ เริ่มจาก normal เสมอเพื่อให้เป็นฐานเปรียบเทียบ
CLASS_ORDER = list(CLASS_LABELS)

_MASS_RE = re.compile(r"^(\d+)g$")
_MM_RE = re.compile(r"^([\d.]+)mm$")


def _parse(path: Path, root: Path) -> dict:
    parts = path.relative_to(root).parts
    cls = parts[0]
    middle = parts[1:-1]

    subclass, mass_g, severity = "", 0, np.nan
    for part in middle:
        if m := _MASS_RE.match(part):
            mass_g = int(m.group(1))
        elif m := _MM_RE.match(part):
            severity = float(m.group(1))
            subclass = part
        else:
            subclass = part

    # imbalance ใช้มวลเป็นตัวบอกความรุนแรง จึงเอามาเป็น subclass ด้วย
    if cls == "imbalance" and not subclass:
        subclass = f"{mass_g}g"

    return {
        "path": path,
        "rel": path.relative_to(root).as_posix(),
        "cls": cls,
        "subclass": subclass,
        "mass_g": mass_g,
        "severity": severity,
        "rot_hz": float(path.stem),
    }


def attach_measured_speed(df: pd.DataFrame) -> pd.DataFrame:
    """ต่อความเร็วที่วัดจาก tachometer เข้ากับดัชนี ถ้ามีตารางอยู่แล้ว

    สร้างตารางนั้นด้วย ``python src/data/scan_speeds.py``
    ถ้ายังไม่มี คอลัมน์ ``rot_hz_measured`` จะเป็น NaN ทั้งหมด และโค้ดที่เรียก
    ต้อง fallback ไปใช้ ``rot_hz`` จากชื่อไฟล์แทน

    **ทำไมต้องมีทั้งสองคอลัมน์** ความเร็วจากชื่อไฟล์คือค่าที่**ตั้งไว้ที่ไดรฟ์**
    ส่วน tachometer วัด**ความเร็วจริงของเพลา** ซึ่งต่ำกว่าอย่างเป็นระบบราว 2.3%
    (น่าจะเป็น slip ของมอเตอร์เหนี่ยวนำ) ความถี่ความเสียหาย BPFO/BSF/FTF
    เป็นตัวคูณของความเร็ว**จริง** ถ้าใช้ชื่อไฟล์จะคลาดไป 2.3% ซึ่งที่ 30 Hz
    คิดเป็น 2 Hz ที่ตำแหน่ง BPFO = ผิดไป 10 ช่องความถี่ของ FFT
    """
    speed_cache = interim_dir() / "mafaulda_speed.csv"
    if not speed_cache.is_file():
        df["rot_hz_measured"] = np.nan
        df["tach_jitter_pct"] = np.nan
        return df

    sp = pd.read_csv(speed_cache)[["rel", "rot_hz_measured", "jitter_pct"]]
    sp = sp.rename(columns={"jitter_pct": "tach_jitter_pct"})
    out = df.merge(sp, on="rel", how="left")

    ratio = out["rot_hz_measured"] / out["rot_hz"]
    out["tach_ok"] = (
        ratio.between(*PLAUSIBLE_RATIO) & (out["tach_jitter_pct"] < MAX_JITTER_PCT)
    )
    return out


# ช่วงอัตราส่วน วัดได้/ชื่อไฟล์ ที่ถือว่าสมเหตุสมผล
# เมื่อใช้ fs = 51,200 Hz ที่ถูกต้อง ค่านี้ควรอยู่ที่ 1.000 (วัดได้ std 0.24%)
# เปิดช่วง ±3% เผื่อความแปรปรวนจริงของความเร็วระหว่างบันทึก
PLAUSIBLE_RATIO = (0.97, 1.03)
MAX_JITTER_PCT = 5.0


def speed_hz(df: pd.DataFrame, fallback_ratio: float | None = None) -> pd.Series:
    """ความเร็วที่ควรใช้คำนวณความถี่ความเสียหาย

    ลำดับการเลือก
        1. ค่าที่วัดจาก tachometer เมื่อผ่านเกณฑ์คุณภาพ (``tach_ok``)
        2. ชื่อไฟล์คูณด้วยอัตราส่วน slip มัธยฐานของ dataset เมื่อวัดไม่ผ่าน
        3. ชื่อไฟล์ดิบ เมื่อยังไม่ได้สแกนเลย

    ข้อ 2 สำคัญ ไฟล์ราว 4% มี tachometer ที่สั่นจนวัดไม่แม่น (กระจุกที่ ``ball_fault``
    ซึ่งเครื่องสั่นแรงที่สุด) การใช้ค่าที่วัดผิดจะแย่กว่าการเดาจากชื่อไฟล์คูณ slip
    เพราะความผิดพลาดของ tachometer ในไฟล์พวกนั้นสูงถึงหลักสิบเปอร์เซ็นต์
    ขณะที่ slip ทั้ง dataset เกาะกลุ่มกันแน่นที่ 2.3% ±0.5%
    """
    if "rot_hz_measured" not in df:
        return df["rot_hz"]

    if fallback_ratio is None:
        ok = df["tach_ok"] if "tach_ok" in df else pd.Series(True, index=df.index)
        ratio = (df.loc[ok, "rot_hz_measured"] / df.loc[ok, "rot_hz"]).median()
        fallback_ratio = float(ratio) if pd.notna(ratio) else 1.0

    good = df["rot_hz_measured"].where(df.get("tach_ok", True))
    return good.fillna(df["rot_hz"] * fallback_ratio)


def build_index(force: bool = False) -> pd.DataFrame:
    """สร้าง (หรืออ่านจาก cache) ตารางดัชนีของไฟล์ทั้งหมด

    cache เก็บที่ ``data/interim/`` ไม่ใช่ ``data/raw/`` เพราะ raw ต้องอ่านอย่างเดียว
    """
    root = mafaulda_dir()
    cache = interim_dir() / INDEX_CACHE

    if cache.is_file() and not force:
        # keep_default_na=False สำคัญ: subclass ของคลาส normal เป็นสตริงว่าง
        # ถ้าปล่อยให้ pandas แปลงเป็น NaN หัวแผงกราฟจะขึ้นคำว่า "nan"
        df = pd.read_csv(cache, keep_default_na=False, na_values=[""])
        df["subclass"] = df["subclass"].fillna("")
        df["severity"] = pd.to_numeric(df["severity"], errors="coerce")
        df["path"] = df["rel"].map(lambda r: root / r)
        return attach_measured_speed(df)

    rows = [_parse(p, root) for p in sorted(root.rglob("*.csv"))]
    if not rows:
        raise FileNotFoundError(f"ไม่พบไฟล์ csv ใต้ {root} — แตก dataset แล้วหรือยัง")

    df = pd.DataFrame(rows)
    df["rot_rpm"] = df["rot_hz"] * 60
    df = df.sort_values(["cls", "subclass", "mass_g", "rot_hz"]).reset_index(drop=True)

    cache.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["path"]).to_csv(cache, index=False)
    return attach_measured_speed(df)


def load(path: Path | str, channels: list[str] | None = None) -> pd.DataFrame:
    """อ่านไฟล์เดียว

    ``channels`` ช่วยให้อ่านเฉพาะคอลัมน์ที่ต้องใช้ ซึ่งเร็วกว่าอ่านทั้ง 8 ช่อง
    อย่างเห็นได้ชัดเมื่อต้องวนหลายสิบไฟล์
    """
    names = mafaulda_columns()
    if channels is None:
        df = pd.read_csv(path, header=None)
        df.columns = names
        return df

    idx = [names.index(c) for c in channels]
    df = pd.read_csv(path, header=None, usecols=idx)
    df.columns = [names[i] for i in sorted(idx)]
    return df[channels]


def pick_matched_speed(
    index: pd.DataFrame,
    target_hz: float,
    cls: str,
    subclass: str | None = None,
    mass_g: int | None = None,
    use_measured: bool = True,
) -> pd.Series:
    """เลือกไฟล์ที่ความเร็วรอบใกล้ ``target_hz`` ที่สุดจากเงื่อนไขที่กำหนด

    **นี่คือฟังก์ชันที่สำคัญที่สุดในโมดูลนี้** ถ้าเทียบกราฟข้ามคลาสโดยไม่คุม
    ความเร็วรอบ สิ่งที่เห็นว่า "ต่างกัน" ส่วนใหญ่คือผลของความเร็วที่ต่างกัน
    ไม่ใช่ผลของความเสียหาย

    ``use_measured=True`` จับคู่ด้วยความเร็วจริงจาก tachometer ซึ่งถูกต้องกว่า
    เพราะชื่อไฟล์เป็นค่าที่ตั้งไว้ที่ไดรฟ์ ไม่ใช่ความเร็วเพลาจริง
    """
    sel = index[index["cls"] == cls]
    if subclass is not None:
        sel = sel[sel["subclass"] == subclass]
    if mass_g is not None:
        sel = sel[sel["mass_g"] == mass_g]

    if sel.empty:
        raise ValueError(
            f"ไม่พบไฟล์ที่ตรงเงื่อนไข cls={cls} subclass={subclass} mass_g={mass_g}"
        )
    key = speed_hz(sel) if use_measured else sel["rot_hz"]
    return sel.loc[(key - target_hz).abs().idxmin()]


def sample_files(
    index: pd.DataFrame,
    cls: str,
    n: int,
    hz_range: tuple[float, float] | None = None,
    mass_g: int | None = None,
    seed: int = 0,
) -> pd.DataFrame:
    """สุ่มไฟล์จากคลาสหนึ่ง ผลซ้ำได้ด้วย seed คงที่"""
    sel = index[index["cls"] == cls]
    if hz_range is not None:
        lo, hi = hz_range
        sel = sel[sel["rot_hz"].between(lo, hi)]
    if mass_g is not None:
        sel = sel[sel["mass_g"] == mass_g]
    if sel.empty:
        return sel
    return sel.sample(n=min(n, len(sel)), random_state=seed)


if __name__ == "__main__":
    idx = build_index(force=True)
    print(f"ไฟล์ทั้งหมด {len(idx)}")
    print()
    print(idx.groupby("cls")["rot_hz"].agg(["count", "min", "max"]).round(3))
    print()
    print("ตัวอย่าง 5 แถว")
    print(idx[["rel", "cls", "subclass", "mass_g", "rot_hz"]].head())

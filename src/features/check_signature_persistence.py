"""ทดสอบว่าลายเซ็นที่ screen_signatures.py หาเจอ เป็นของความเสียหายจริง หรือเป็นของรอบบันทึก

**ปัญหา** ใน MAFAULDA แต่ละกลุ่มย่อยน่าจะถูกบันทึกรวดเดียวในการติดตั้งครั้งเดียว
อะไรก็ตามที่ต่างกันระหว่างรอบบันทึก (การขันเซ็นเซอร์ การประกอบเครื่อง ระดับ noise)
จะแยกกลุ่มได้ขาด 100% ทั้งที่ไม่เกี่ยวกับความเสียหาย AUC = 1.0 จึงพิสูจน์อะไรไม่ได้

**หลักการทดสอบ** ลายเซ็นของความเสียหายจริงต้องผ่านอย่างน้อยหนึ่งข้อ
    1. คงอยู่ข้ามรอบบันทึก — bearing แต่ละชนิดมีบันทึกไว้ที่มวลถ่วง 0/6/20/35 g
       ซึ่งเป็นคนละรอบ ถ้าเป็นผลของรอยแตก ควรเห็นทุกระดับ
    2. เปลี่ยนตามความรุนแรงอย่างเป็นระบบ — imbalance (6→35 g), misalignment (mm)

ถ้าเจอแค่ในรอบเดียวแล้วหายไปในรอบอื่น = ลายเซ็นของรอบบันทึก ไม่ใช่ของความเสียหาย

รัน:
    python src/features/check_signature_persistence.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.features.screen_signatures import HZ_RANGE, channel_features  # noqa: E402
from src.paths import repo_root  # noqa: E402

PER_LEVEL = 8

# (ชื่อ, ลายเซ็นที่ตรวจ "ช่อง.feature", cls, subclass, ระดับ, คอลัมน์ที่ใช้แยกระดับ)
CHECKS = [
    ("under cage", "u_tang.kurt", "underhang", "cage_fault", [0, 6, 20, 35], "mass_g"),
    ("over cage", "o_tang.env_floor", "overhang", "cage_fault", [0, 6, 20, 35], "mass_g"),
    ("under outer", "o_axial.e_high", "underhang", "outer_race", [0, 6, 20, 35], "mass_g"),
    ("over outer", "u_radial.env_rel", "overhang", "outer_race", [0, 6, 20, 35], "mass_g"),
    ("under ball", "o_axial.rms", "underhang", "ball_fault", [0, 6, 20, 35], "mass_g"),
    ("over ball", "o_radial.e_high", "overhang", "ball_fault", [0, 6, 20, 35], "mass_g"),
    ("imbalance", "u_radial.h1_frac", "imbalance", None, [6, 10, 15, 20, 25, 30, 35], "mass_g"),
    ("imbalance", "o_axial.rms", "imbalance", None, [6, 10, 15, 20, 25, 30, 35], "mass_g"),
    ("h-misalign", "u_tang.e_high", "horizontal-misalignment", None,
     ["0.5mm", "1.0mm", "1.5mm", "2.0mm"], "subclass"),
    ("v-misalign", "u_tang.kurt_band", "vertical-misalignment", None,
     ["0.51mm", "0.63mm", "1.27mm", "1.40mm", "1.78mm", "1.90mm"], "subclass"),
]


def feature_values(rows: pd.DataFrame, feat: str) -> np.ndarray:
    ch, name = feat.split(".")
    out = []
    for _, r in rows.iterrows():
        rot = float(mf.speed_hz(r.to_frame().T).iloc[0])
        x = mf.load(r["path"], [ch])[ch].to_numpy()
        out.append(channel_features(x, rot)[name])
    return np.array(out)


def main() -> int:
    idx = mf.build_index()
    idx = idx[idx["rot_hz"].between(*HZ_RANGE)]
    normal = idx[idx["cls"] == "normal"]

    lines = [
        "# ลายเซ็นเป็นของความเสียหาย หรือของรอบบันทึก",
        "",
        f"- วันที่: {date.today().isoformat()}",
        "- สคริปต์: `src/features/check_signature_persistence.py`",
        f"- ความเร็ว {HZ_RANGE[0]:.0f}–{HZ_RANGE[1]:.0f} Hz · ระดับละไม่เกิน {PER_LEVEL} ไฟล์",
        "- ตัวเลขในตาราง = มัธยฐานของระดับนั้น หารด้วยมัธยฐานของ normal",
        "- `*` = ช่วงค่าของระดับนั้นไม่เหลื่อมกับ normal เลย",
        "",
    ]
    cache: dict[str, np.ndarray] = {}
    for group, feat, cls, sub, levels, key in CHECKS:
        if feat not in cache:
            cache[feat] = feature_values(normal, feat)
        nv = cache[feat]
        nmed, nlo, nhi = np.median(nv), nv.min(), nv.max()

        cells = []
        for lv in levels:
            s = idx[idx["cls"] == cls]
            if sub is not None:
                s = s[s["subclass"] == sub]
            s = s[s[key] == lv]
            s = s.sample(n=min(PER_LEVEL, len(s)), random_state=0)
            if s.empty:
                cells.append("—")
                continue
            v = feature_values(s, feat)
            sep = v.min() > nhi or v.max() < nlo
            cells.append(f"{np.median(v) / nmed:.2f}{'\\*' if sep else ''}")
        head = " | ".join(f"{lv}g" if key == "mass_g" else str(lv) for lv in levels)
        lines += [f"### {group} — `{feat}`", "",
                  f"| {head} |", "|" + "---:|" * len(levels),
                  f"| {' | '.join(cells)} |", ""]
        print(f"{group:12s} {feat:20s} " + "  ".join(cells), flush=True)

    out = repo_root() / "experiments" / f"{date.today().isoformat()}-signature-persistence.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานลง {out.relative_to(repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

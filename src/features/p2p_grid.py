"""คำนวณความสูงยอดถึงยอด (peak-to-peak) ของทุกไฟล์ทุกช่อง เก็บเป็นตารางไว้ใช้ซ้ำ

เป็นขั้นเตรียมข้อมูลให้ `src/viz/bubble_grid.py` ซึ่งต้องวาดจุดหลายร้อยจุดพร้อมกัน
ถ้าให้แอปอ่าน CSV สดตอนเปลี่ยนช่องเซ็นเซอร์จะรอเป็นนาทีทุกครั้ง สคริปต์นี้ทำครั้งเดียว
ราว 8–12 นาที แล้วแอปเปิดได้ทันที

**ตัวเลขที่เก็บคือมัธยฐานของ peak-to-peak รายหน้าต่าง ไม่ใช่ของทั้งไฟล์**

ถ้าเอา max − min ของทั้งไฟล์ 250,000 แถว ตัวเลขจะถูกกำหนดโดยสไปก์เดียวที่แรงที่สุด
ในไฟล์ ซึ่งอาจเป็นสัญญาณรบกวนชั่วขณะ ไม่ใช่ลักษณะของความเสียหาย วิธีที่ใช้คือ
ตัดไฟล์เป็นหน้าต่าง 67 ms (เท่ากับที่ `browse_waveforms.py` วาดบนจอ) ได้ 72 หน้าต่าง
คิด peak-to-peak ทีละหน้าต่างแล้วเอามัธยฐาน

จึงเป็นตัวเลขเดียวกับที่มุมขวาบนของ `browse_waveforms.py` **แต่วัดทั้งไฟล์แทนที่จะ
วัดหน้าต่างเดียว** ซึ่งต่างกันจริง เช่น underhang outer race ช่อง o_radial
หน้าต่างเดียวได้ 17.72 เท่า แต่วัดหลายไฟล์ทั้งไฟล์ได้ 21.83 เท่า

รัน:
    python src/features/p2p_grid.py          # คำนวณใหม่ทั้งหมด
    python src/features/p2p_grid.py --limit 50   # ลองกับไฟล์น้อยๆ ก่อน
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.paths import processed_dir, repo_root, sampling_rate  # noqa: E402
from src.viz.explore_raw_channels import CHANNELS  # noqa: E402

FS = sampling_rate()
WINDOW_MS = 67.0
OUT_NAME = "p2p_grid.csv"


def file_p2p(d: pd.DataFrame, win: int) -> dict[str, float]:
    """มัธยฐานของ peak-to-peak รายหน้าต่าง ของทุกช่องในไฟล์เดียว"""
    out = {}
    for ch in CHANNELS:
        x = d[ch].to_numpy()
        n = len(x) // win
        seg = x[:n * win].reshape(n, win)
        out[f"p2p_{ch}"] = float(np.median(seg.max(axis=1) - seg.min(axis=1)))
    return out


def build(index: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
    win = int(WINDOW_MS / 1000.0 * FS)
    rows_in = index if limit is None else index.head(limit)
    speeds = mf.speed_hz(rows_in)
    total = len(rows_in)
    print(f"คำนวณ peak-to-peak จาก {total} ไฟล์ "
          f"หน้าต่าง {win} แถว ({WINDOW_MS:.0f} ms)")

    out, t0 = [], time.time()
    for i, (idx_i, r) in enumerate(rows_in.iterrows(), start=1):
        d = mf.load(r["path"], CHANNELS)
        row = {
            "rel": r["rel"], "cls": r["cls"], "subclass": r["subclass"],
            "mass_g": r["mass_g"], "severity": r["severity"],
            "rot_hz": r["rot_hz"], "rot_hz_used": float(speeds.loc[idx_i]),
        }
        row.update(file_p2p(d, win))
        out.append(row)
        if i % 100 == 0 or i == total:
            done = time.time() - t0
            print(f"  {i}/{total}  ผ่านไป {done / 60:.1f} นาที  "
                  f"เหลืออีกราว {(done / i) * (total - i) / 60:.1f} นาที", flush=True)
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="ตาราง peak-to-peak ของทุกไฟล์ทุกช่อง")
    ap.add_argument("--limit", type=int, default=None, help="จำกัดจำนวนไฟล์ ไว้ทดสอบ")
    args = ap.parse_args()

    tab = build(mf.build_index(), args.limit)
    out = processed_dir() / OUT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out, index=False)

    print(f"\nเขียน {len(tab)} แถวลง {out.relative_to(repo_root())}")
    print(tab.groupby("cls")[[f"p2p_{c}" for c in CHANNELS]].median().round(4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

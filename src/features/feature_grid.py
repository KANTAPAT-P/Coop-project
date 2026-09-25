"""คำนวณ feature ทุกตัวของทุกช่อง ของทุกไฟล์ เก็บเป็นตารางเดียวไว้ให้ bubble_grid ใช้

ขยายจาก `p2p_grid.py` ซึ่งคำนวณเฉพาะ peak-to-peak (= ความสูงของกราฟ raw)
ไฟล์นี้คำนวณครบทั้ง 12 ปริมาณ × 6 ช่อง = 72 คอลัมน์ ทำให้ `bubble_grid.py`
เลือกได้ว่าจะพล็อต feature ตัวไหน ไม่ใช่แค่ความแรงอย่างเดียว

**ทำไมสำคัญ** ลายเซ็นของ misalignment คือ `o_tang.r21` (อัตราส่วนพีค 2×/1×)
ซึ่ง**ไม่เกี่ยวกับความแรง**เลย misalignment ย้ายพลังงานจาก 1× ไป 2× โดยที่
ความแรงรวมเท่าเดิม กราฟที่พล็อต p2p จึงมองลายเซ็นตัวนี้ไม่เห็นตามนิยาม

## ข้อควรระวังที่บังคับไว้ในโค้ดนี้แล้ว

1. **ไม่รวมช่อง `mic`** เพราะสเกลของคลาส imbalance ต่างจากคลาสอื่น 88 เท่า
   ซึ่งเป็น data leakage ชัดๆ (CLAUDE.md หัวข้อ 5)
2. **feature คำนวณจากไฟล์เต็ม 250,000 แถว** ไม่ใช่หน้าต่างสั้น เพื่อให้ได้
   ความละเอียดความถี่ 0.2048 Hz และให้ตัวเลขตรงกับ `screen_signatures.py`
   ที่ใช้สรุปลายเซ็นไว้ ถ้าเปลี่ยนความยาวไป ตัวเลขจะเทียบกับการทดลองไม่ได้
3. **ความเร็วรอบใช้ค่าจาก tachometer** ผ่าน `mf.speed_hz()` ไม่ใช่ชื่อไฟล์ดิบ
   เพราะ `h1_frac` และ `r21` ต้องรู้ว่า 1× อยู่ตรงไหนจริงๆ
4. **p2p คิดเป็นมัธยฐานของหน้าต่าง 67 ms** เหมือนเดิม ไม่ใช่ max−min ทั้งไฟล์
   ตัวเลขจึงเทียบกับตารางเดิมและกับ `browse_waveforms.py` ได้

⚠️ **feature ทั้งหมดผ่าน high-pass 10 Hz** ตาม `channel_features` ที่ไฟล์ละ 10 Hz
ตัดทิ้งเพื่อกัน drift ของเซ็นเซอร์ ที่ความเร็วรอบต่ำกว่า ~15 Hz พีค 1× จะเริ่ม
ถูกกรองกินไปบ้าง `h1_frac` และ `r21` ที่ปลายล่างของแกนจึงอ่านด้วยความระวัง
`bubble_grid.py` ขีดเส้นบอกช่วงที่คัดกรองลายเซ็นไว้ (20–42 Hz) ให้แล้ว

รัน:
    python src/features/feature_grid.py --limit 20    # ลองจับเวลาก่อน
    python src/features/feature_grid.py               # เต็มชุด ใช้เวลานาน
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
from src.features.p2p_grid import WINDOW_MS  # noqa: E402
from src.features.screen_signatures import channel_features  # noqa: E402
from src.paths import processed_dir, repo_root, sampling_rate  # noqa: E402
from src.viz.explore_raw_channels import CHANNELS  # noqa: E402

FS = sampling_rate()
OUT_NAME = "feature_grid.csv"

# ชื่อ feature ที่ channel_features คืนมา บวก p2p ที่คำนวณเพิ่มเอง
FEATURES = ["p2p", "rms", "kurt", "crest", "h1_frac", "r21",
            "e_low", "e_mid", "e_high", "kurt_band", "env_floor", "env_rel"]


def window_p2p(x: np.ndarray, win: int) -> float:
    """มัธยฐานของ peak-to-peak รายหน้าต่าง — ตัวเดียวกับที่ browse_waveforms แสดง"""
    n = len(x) // win
    seg = x[:n * win].reshape(n, win)
    return float(np.median(seg.max(axis=1) - seg.min(axis=1)))


def build(index: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
    win = int(WINDOW_MS / 1000.0 * FS)
    rows_in = index if limit is None else index.head(limit)
    speeds = mf.speed_hz(rows_in)
    total = len(rows_in)
    print(f"คำนวณ {len(FEATURES)} feature × {len(CHANNELS)} ช่อง จาก {total} ไฟล์")

    out, t0 = [], time.time()
    for i, (idx_i, r) in enumerate(rows_in.iterrows(), start=1):
        rot = float(speeds.loc[idx_i])
        d = mf.load(r["path"], CHANNELS)
        row = {
            "rel": r["rel"], "cls": r["cls"], "subclass": r["subclass"],
            "mass_g": r["mass_g"], "severity": r["severity"],
            "rot_hz": r["rot_hz"], "rot_hz_used": rot,
        }
        for ch in CHANNELS:
            x = d[ch].to_numpy()
            row[f"{ch}.p2p"] = window_p2p(x, win)
            for k, v in channel_features(x, rot).items():
                row[f"{ch}.{k}"] = v
        out.append(row)
        if i % 50 == 0 or i == total:
            done = time.time() - t0
            print(f"  {i}/{total}  ผ่านไป {done / 60:.1f} นาที  "
                  f"เหลืออีกราว {(done / i) * (total - i) / 60:.1f} นาที", flush=True)
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="ตาราง feature ทุกตัวของทุกไฟล์")
    ap.add_argument("--limit", type=int, default=None, help="จำกัดจำนวนไฟล์ ไว้จับเวลา")
    args = ap.parse_args()

    tab = build(mf.build_index(), args.limit)
    out = processed_dir() / OUT_NAME
    out.parent.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out, index=False)
    print(f"\nเขียน {len(tab)} แถว × {len(tab.columns)} คอลัมน์ "
          f"ลง {out.relative_to(repo_root())}")

    miss = tab[[c for c in tab.columns if "." in c]].isna().sum()
    if miss.any():
        print("\n⚠️ คอลัมน์ที่มีค่าว่าง (ปกติมาจาก r21 ตอนหาพีค 1× ไม่เจอ)")
        print(miss[miss > 0].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

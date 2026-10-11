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


def search_tol_hz(n: int, rot: float, fs: float = FS) -> float:
    """ความกว้างหน้าต่างค้นพีค 1x/2x เป็น Hz สัมบูรณ์

    ค่าเริ่มต้นของ `channel_features` คือ 2% ของความเร็วรอบ ซึ่ง**ใช้กับหน้าต่าง
    สั้นไม่ได้** เพราะ 2% ของ 30 Hz = 0.6 Hz แคบกว่าหนึ่งช่องความถี่ของหน้าต่าง
    410 ms (2.44 Hz) หน้าต่างค้นจะว่างเปล่าแล้วคืนแอมพลิจูด 0
    วัดแล้วว่าทำให้ `r21` คำนวณได้แค่ 65.5% และ bias เป็น -26.9%

    จึงใช้ **ค่าที่กว้างกว่าระหว่าง 2% ของความเร็วรอบ กับ 2 ช่องความถี่**
    สองช่องเพราะหน้าต่าง Hann ทำให้พีคเดียวแผ่ออกไปราวสองช่องต่อข้าง
    """
    return max(0.02 * rot, 2.0 * fs / n)


def build(index: pd.DataFrame, limit: int | None = None,
          window_ms: float | None = None) -> pd.DataFrame:
    """ตาราง feature ของทุกไฟล์

    ``window_ms`` ค่าเริ่มต้น ``None`` = คำนวณจากไฟล์เต็ม ซึ่งเป็นพฤติกรรมเดิม
    ถ้าใส่ค่า จะตัดไฟล์เป็นหน้าต่างยาวเท่านั้น **แล้วคืนหนึ่งแถวต่อหนึ่งหน้าต่าง**
    พร้อมคอลัมน์ ``win`` บอกลำดับ และ ``win_fs`` / ``win_n`` บอกหน้าต่างที่ใช้
    เพื่อให้ไฟล์อธิบายตัวเองได้ ไม่ต้องจำจากชื่อไฟล์

    🚨 **หนึ่งแถวต่อหน้าต่าง ไม่ใช่หนึ่งแถวต่อไฟล์ จึงต้องแบ่ง train/test ตาม
    คอลัมน์ `rel` เสมอ** หน้าต่างที่ติดกันจากไฟล์เดียวกันคล้ายกันเองมากกว่า
    ความต่างระหว่างไฟล์ 2-25 เท่า ถ้าสุ่มแถวจะเป็น leakage ตัวเดียวกับที่
    วัดไว้ว่ากินไป 27 จุด accuracy (`experiments/2026-09-25-split-leakage.md`)
    """
    sub = int(WINDOW_MS / 1000.0 * FS)        # หน้าต่างย่อย 67 ms ของ p2p
    n_win = None if window_ms is None else int(round(window_ms / 1000.0 * FS))
    if n_win is not None and n_win < sub:
        raise SystemExit(f"หน้าต่าง {window_ms:.0f} ms สั้นกว่าหน้าต่างย่อยของ "
                         f"p2p ({WINDOW_MS:.0f} ms) จึงคำนวณ p2p ไม่ได้")

    rows_in = index if limit is None else index.head(limit)
    speeds = mf.speed_hz(rows_in)
    total = len(rows_in)
    if n_win is None:
        print(f"คำนวณ {len(FEATURES)} feature × {len(CHANNELS)} ช่อง "
              f"จาก {total} ไฟล์ (ไฟล์เต็ม 250,000 แถว)")
    else:
        print(f"คำนวณ {len(FEATURES)} feature × {len(CHANNELS)} ช่อง "
              f"จาก {total} ไฟล์")
        print(f"หน้าต่าง {n_win:,} แถว = {n_win / FS * 1000:.1f} ms "
              f"| ความละเอียดความถี่ {FS / n_win:.2f} Hz "
              f"| ตัดได้ {250_000 // n_win} หน้าต่างต่อไฟล์")

    out, t0 = [], time.time()
    for i, (idx_i, r) in enumerate(rows_in.iterrows(), start=1):
        rot = float(speeds.loc[idx_i])
        d = mf.load(r["path"], CHANNELS)
        meta = {
            "rel": r["rel"], "cls": r["cls"], "subclass": r["subclass"],
            "mass_g": r["mass_g"], "severity": r["severity"],
            "rot_hz": r["rot_hz"], "rot_hz_used": rot,
        }
        cols = {ch: d[ch].to_numpy() for ch in CHANNELS}
        n_full = len(next(iter(cols.values())))
        if n_win is None:
            spans = [(0, n_full, 0)]
            tol = None
        else:
            spans = [(s, s + n_win, w) for w, s
                     in enumerate(range(0, n_full - n_win + 1, n_win))]
            tol = search_tol_hz(n_win, rot)
        for lo, hi, w in spans:
            row = dict(meta)
            if n_win is not None:
                row |= {"win": w, "win_fs": FS, "win_n": n_win}
            for ch in CHANNELS:
                x = cols[ch][lo:hi]
                row[f"{ch}.p2p"] = window_p2p(x, sub)
                for k, v in channel_features(x, rot, tol_hz=tol).items():
                    row[f"{ch}.{k}"] = v
            out.append(row)
        if i % 50 == 0 or i == total:
            done = time.time() - t0
            print(f"  {i}/{total}  ผ่านไป {done / 60:.1f} นาที  "
                  f"เหลืออีกราว {(done / i) * (total - i) / 60:.1f} นาที", flush=True)
    return pd.DataFrame(out)


def grid_for_window(window: dict | None) -> Path:
    """ไฟล์ตาราง feature ที่ตรงกับหน้าต่างที่กำหนด

    🚨 **ทุกสคริปต์ที่โหลดโมเดลต้องใช้ฟังก์ชันนี้เลือกตาราง** ไม่ใช่เขียน
    `feature_grid.csv` ตายตัว เพราะค่าของตัวชี้วัดขึ้นกับความยาวหน้าต่าง
    ถ้าโมเดลเทรนด้วย 410 ms แต่ป้อนค่าจากไฟล์เต็ม 4,883 ms เข้าไป
    **ไฟล์ปกติจะถูกตัดสินว่าผิดปกติ โดยไม่มี error ใดๆ**

    ตรรกะนี้อยู่ที่นี่ที่เดียว เพราะเคยก๊อปไว้หลายที่แล้วแต่ละที่ล้าหลัง
    กันเองคนละจังหวะ ซึ่งเป็นรูปแบบเดียวกับกฎข้อ 6 ใน `CLAUDE.md`

    ``window`` เป็น ``None`` หรือชี้ที่ไฟล์เต็ม -> `feature_grid.csv`
    """
    if not window:
        return processed_dir() / OUT_NAME
    ms = float(window["n"]) / float(window["fs"]) * 1000.0
    if int(round(float(window["n"]))) >= 250_000:
        return processed_dir() / OUT_NAME
    return processed_dir() / out_name(ms)


def require_grid_for_window(window: dict | None) -> Path:
    """เหมือน ``grid_for_window`` แต่ถ้าไม่มีไฟล์ ให้บอกวิธีสร้างแล้วจบ"""
    p = grid_for_window(window)
    if not p.is_file():
        hint = "python src/features/feature_grid.py"
        if window and int(round(float(window["n"]))) < 250_000:
            hint += f" --window-ms {float(window['n']) / float(window['fs']) * 1000:.1f}"
        raise SystemExit(f"ไม่พบ {p}\nสร้างก่อนด้วย: {hint}")
    return p


def out_name(window_ms: float | None, partial: bool = False) -> str:
    """ชื่อไฟล์ผลลัพธ์ **ต้องต่างกันตามหน้าต่าง** ไม่ใช่เขียนทับกัน

    `feature_grid.csv` ของไฟล์เต็มเป็นที่มาของตัวเลขในเอกสารหลายฉบับและของ
    `bubble_grid.py` ถ้าเขียนทับด้วยตารางหน้าต่างสั้น กราฟและเอกสารจะเปลี่ยน
    ความหมายเงียบๆ โดยไม่มีใครรู้

    🚨 ``partial=True`` (มาจาก ``--limit``) ต่อท้ายชื่อว่า ``-partial``
    **เพราะเคยพลาดมาแล้วจริง** รัน ``--limit 1`` เพื่อลองจับเวลา แล้วมันเขียนทับ
    `feature_grid.csv` ที่มี 1,951 แถวให้เหลือ **1 แถว** โดยไม่เตือนอะไร
    ต้องสร้างใหม่ทั้งชุด

    > **แฟล็กที่ตั้งใจให้ใช้ "ลองดูก่อน" ต้องไม่เขียนทับของจริง**
    > ไม่งั้นการลองดูก่อนจะกลายเป็นการทำลาย
    """
    base = OUT_NAME if window_ms is None else f"feature_grid_win{round(window_ms)}ms.csv"
    if partial:
        return base.replace(".csv", "-partial.csv")
    return base


def main() -> int:
    ap = argparse.ArgumentParser(description="ตาราง feature ทุกตัวของทุกไฟล์")
    ap.add_argument("--limit", type=int, default=None,
                    help="จำกัดจำนวนไฟล์ ไว้จับเวลา "
                         "(ผลออกไฟล์ชื่อ ...-partial.csv ไม่เขียนทับของจริง)")
    ap.add_argument("--window-ms", type=float, default=None,
                    help="ตัดไฟล์เป็นหน้าต่างยาวเท่านี้ แล้วคืนหนึ่งแถวต่อหน้าต่าง "
                         "ไม่ใส่ = ใช้ไฟล์เต็ม (พฤติกรรมเดิม)")
    args = ap.parse_args()

    tab = build(mf.build_index(), args.limit, args.window_ms)
    out = processed_dir() / out_name(args.window_ms, partial=args.limit is not None)
    if args.limit is not None:
        print(f"⚠️ --limit {args.limit} -> เขียนลงไฟล์ชั่วคราว ไม่ทับของจริง")
    out.parent.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out, index=False)
    print(f"\nเขียน {len(tab):,} แถว × {len(tab.columns)} คอลัมน์ "
          f"ลง {out.relative_to(repo_root())}")
    if args.window_ms is not None:
        print(f"  = {tab.rel.nunique():,} ไฟล์ × {len(tab) / tab.rel.nunique():.0f} "
              f"หน้าต่าง  ⚠️ แบ่ง train/test ตามคอลัมน์ `rel` เท่านั้น")

    miss = tab[[c for c in tab.columns if "." in c]].isna().sum()
    if miss.any():
        print("\n⚠️ คอลัมน์ที่มีค่าว่าง (ปกติมาจาก r21 ตอนหาพีค 1× ไม่เจอ)")
        print(miss[miss > 0].to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

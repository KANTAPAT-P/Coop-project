"""วัดความเร็วรอบจริงจาก tachometer ของทุกไฟล์ แล้วเก็บเป็นตาราง

ผลลัพธ์ไปที่ ``data/interim/mafaulda_speed.csv`` ซึ่งเป็นโฟลเดอร์ที่เขียนได้
ไม่แตะ ``data/raw`` ตามกฎข้อ 1 ของ CLAUDE.md

**ทำไมต้องเก็บเป็นตาราง** การอ่าน tachometer ของทั้ง 1,951 ไฟล์ใช้เวลาหลายนาที
ถ้าทุกสคริปต์ต้องคำนวณใหม่เองทุกครั้งจะช้าจนไม่มีใครอยากใช้ เก็บครั้งเดียวแล้ว
ให้ ``mafaulda.build_index()`` เอาไปต่อกับดัชนีหลักได้เลย

**เรื่องความเร็วในการอ่าน** ไม่จำเป็นต้องอ่านทั้ง 250,000 แถวเพื่อวัดความเร็ว
อ่านแค่ 2 วินาทีแรกก็ได้พัลส์อย่างน้อย 24 ครั้งแม้ที่ความเร็วต่ำสุด 12 Hz
ซึ่งพอสำหรับหามัธยฐานที่เสถียร เพราะ jitter ของสัญญาณนี้ต่ำกว่า 1%
ตัวเลือก ``--nrows 0`` บังคับให้อ่านเต็มไฟล์ถ้าต้องการความละเอียดสูงสุด

รัน:
    python src/data/scan_speeds.py
    python src/data/scan_speeds.py --nrows 0 --limit 50
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.data import tachometer as tach  # noqa: E402
from src.paths import interim_dir, sampling_rate  # noqa: E402

SPEED_CACHE = "mafaulda_speed.csv"


def scan(index: pd.DataFrame, nrows: int | None, progress_every: int = 100) -> pd.DataFrame:
    fs = sampling_rate()
    rows = []
    t0 = time.perf_counter()

    for i, (_, r) in enumerate(index.iterrows(), start=1):
        x = pd.read_csv(r["path"], header=None, usecols=[0], nrows=nrows)[0].to_numpy()
        res = tach.analyse(x, fs)
        rows.append({
            "rel": r["rel"],
            "rot_hz_nominal": r["rot_hz"],
            "rot_hz_measured": res.rot_hz,
            "n_pulses": res.n_pulses,
            "jitter_pct": res.jitter_pct,
            "duty_pct": res.duty_pct,
        })
        if i % progress_every == 0 or i == len(index):
            el = time.perf_counter() - t0
            print(f"  {i}/{len(index)}  ({el:.0f} วินาที, เหลืออีกราว "
                  f"{el / i * (len(index) - i):.0f} วินาที)", flush=True)

    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="วัดความเร็วรอบจริงของทุกไฟล์")
    ap.add_argument("--nrows", type=int, default=100_000,
                    help="อ่านกี่แถวต่อไฟล์ (0 = อ่านเต็ม 250,000 แถว)")
    ap.add_argument("--limit", type=int, default=0, help="จำกัดจำนวนไฟล์ ไว้ทดสอบ")
    args = ap.parse_args()

    index = mf.build_index()
    if args.limit:
        index = index.head(args.limit)

    nrows = None if args.nrows == 0 else args.nrows
    print(f"สแกน {len(index)} ไฟล์ อ่านไฟล์ละ {nrows or 250_000} แถว")

    df = scan(index, nrows)

    out = interim_dir() / SPEED_CACHE
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nเขียนลง {out}")

    ratio = df["rot_hz_measured"] / df["rot_hz_nominal"]
    print()
    print("=== สรุป ===")
    print(f"อัตราส่วน วัดได้/ชื่อไฟล์ : {ratio.min():.5f} – {ratio.max():.5f} "
          f"(มัธยฐาน {ratio.median():.5f})")
    print(f"jitter                  : มัธยฐาน {df['jitter_pct'].median():.3f}% "
          f"สูงสุด {df['jitter_pct'].max():.3f}%")
    bad = df[df["jitter_pct"] > 5.0]
    print(f"ไฟล์ที่ jitter เกิน 5%    : {len(bad)}")
    if len(bad):
        print(bad[["rel", "rot_hz_nominal", "rot_hz_measured", "jitter_pct", "n_pulses"]]
              .head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

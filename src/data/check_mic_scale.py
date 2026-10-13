"""ตรวจข้ออ้างใน CLAUDE.md ว่า mic ในคลาส imbalance มีสเกลสูงกว่าคลาสอื่น 88 เท่า

สุ่ม 3 ไฟล์แล้วไม่เห็นผลนั้น จึงต้องวัดทั้งคลาส ไม่ใช่สรุปจากตัวอย่างเล็ก
และวัดแยกตามมวลถ่วงกับความเร็วรอบ ซึ่งเป็นวิธีแยกสองสมมติฐานที่
CLAUDE.md หัวข้อ 6 ระบุไว้

- ถ้าเป็น gain ของ preamp ที่ตั้งต่างกัน -> ทุกไฟล์ในคลาสจะสูงเท่าๆ กัน
- ถ้าเป็นเสียงจริงจากการสั่น -> จะเพิ่มตามมวลถ่วงและความเร็วรอบ
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data import mafaulda  # noqa: E402

idx = mafaulda.build_index()
sub = idx[idx.cls.isin(["normal", "imbalance"])]
print("อ่าน", len(sub), "ไฟล์ (normal + imbalance) ช่อง mic อย่างเดียว")

rows = []
for r in sub.itertuples():
    x = mafaulda.load(r.path, channels=["mic"])["mic"].to_numpy()
    rows.append({"cls": r.cls, "mass_g": r.mass_g, "rot_hz": r.rot_hz,
                 "rng": float(x.max() - x.min()), "rms": float(np.sqrt((x ** 2).mean()))})
d = pd.DataFrame(rows)

print("\nพิสัย peak-to-peak ของ mic")
print(f"{'คลาส/มวล':20s} {'ไฟล์':>5s} {'มัธยฐาน':>10s} {'ต่ำสุด':>9s} {'สูงสุด':>10s}")
n_med = d.loc[d.cls == "normal", "rng"].median()
print(f"{'normal':20s} {len(d[d.cls=='normal']):5d} {n_med:10.3f} "
      f"{d.loc[d.cls=='normal','rng'].min():9.3f} {d.loc[d.cls=='normal','rng'].max():10.3f}")
for m, g in d[d.cls == "imbalance"].groupby("mass_g"):
    print(f"{'imbalance ' + str(int(m)) + ' g':20s} {len(g):5d} {g.rng.median():10.3f} "
          f"{g.rng.min():9.3f} {g.rng.max():10.3f}   = {g.rng.median()/n_med:6.2f} เท่าของ normal")

big = d[(d.cls == "imbalance") & (d.rng > 10 * n_med)]
print(f"\nไฟล์ imbalance ที่พิสัยเกิน 10 เท่าของ normal: {len(big)} จาก {len(d[d.cls=='imbalance'])}")
if len(big):
    print("  มวลถ่วงที่พบ :", sorted(big.mass_g.unique().tolist()))
    print("  ความเร็วรอบ  : %.2f .. %.2f Hz" % (big.rot_hz.min(), big.rot_hz.max()))
    print("  เทียบกับทั้งคลาส: %.2f .. %.2f Hz" %
          (d[d.cls == 'imbalance'].rot_hz.min(), d[d.cls == 'imbalance'].rot_hz.max()))

imb = d[d.cls == "imbalance"]
print("\nสหสัมพันธ์อันดับของพิสัย mic ในคลาส imbalance")
print(f"  กับมวลถ่วง     {imb.rng.corr(imb.mass_g, method='spearman'):+.3f}")
print(f"  กับความเร็วรอบ {imb.rng.corr(imb.rot_hz, method='spearman'):+.3f}")

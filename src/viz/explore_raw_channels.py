"""สำรวจสัญญาณดิบทุกช่องเซ็นเซอร์ แยกเป็น 4 รูปตามกลุ่มความเสียหาย

**คำถามที่ชุดนี้ตอบ** มีช่องเซ็นเซอร์ไหนบ้างที่ทำให้ความเสียหาย**มองเห็นได้ด้วยตาเปล่า**
ในโดเมนเวลา รูปหลักในรายงานใช้ `u_radial` ช่องเดียว ซึ่งภายหลังพบว่ามองไม่เห็น
misalignment เลย ชุดนี้จึงวางทุกช่องให้เห็นพร้อมกัน

    00a  Normal กับ imbalance
    00b  Normal กับ horizontal / vertical misalignment
    00c  Normal กับ underhang bearing แยก 3 ชนิด
    00d  Normal กับ overhang bearing แยก 3 ชนิด

**กติกา**
- แถว = ช่องเซ็นเซอร์ คอลัมน์ = กลุ่ม คอลัมน์แรกเป็น normal เสมอ
- ความเร็วรอบจับคู่ใกล้ ``--target-hz`` ด้วยความเร็วจาก tachometer
  และพิมพ์ความเร็วจริง ระยะเยื้อง (mm) หรือมวลถ่วง (g) ไว้บนหัวคอลัมน์
- bearing ใช้มวลถ่วง 0 g เพื่อไม่ให้ imbalance ปน
- **แกน y ร่วมกันทั้งแถว** เทียบข้ามคอลัมน์ได้ แต่ไม่ร่วมข้ามแถว
  เพราะแต่ละช่องระดับสัญญาณต่างกันมาก โดยเฉพาะ o_radial
- ตัวเลขมุมขวาบนคือ peak-to-peak เทียบกับ normal ในช่องเดียวกัน

⚠️ รูปพวกนี้เป็น**ไฟล์เดียวต่อกลุ่ม** ใช้หาจุดที่น่าสงสัยเท่านั้น
ตัวเลขทุกตัวต้องยืนยันด้วยหลายไฟล์ก่อนสรุป (เคยเจอไฟล์เดียวให้ 17.7 เท่า
แต่พอวัด 10 ไฟล์เหลือ 3.1 เท่า)

รัน:
    python src/viz/explore_raw_channels.py
    python src/viz/explore_raw_channels.py --target-hz 45 --window-ms 40
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.paths import repo_root, sampling_rate  # noqa: E402
from src.viz import style  # noqa: E402
from src.viz.make_eda_report import IMBALANCE_MASS_G, _rot  # noqa: E402

FS = sampling_rate()
OUT = repo_root() / "reports" / "eda"

# ไม่รวม mic เพราะสเกลเพี้ยน 88 เท่าในคลาส imbalance
CHANNELS = ["u_axial", "u_radial", "u_tang", "o_axial", "o_radial", "o_tang"]

# (ชื่อบนหัวคอลัมน์, cls, subclass, mass_g)
NORMAL = ("Normal", "normal", None, None)
FIGURES = {
    "00a-raw-imbalance": (
        "Normal vs imbalance",
        [NORMAL, (f"Imbalance {IMBALANCE_MASS_G} g", "imbalance", None, IMBALANCE_MASS_G)],
    ),
    "00b-raw-misalignment": (
        "Normal vs misalignment",
        [NORMAL,
         ("Horizontal misalign 2.0 mm", "horizontal-misalignment", "2.0mm", None),
         ("Vertical misalign 1.90 mm", "vertical-misalignment", "1.90mm", None)],
    ),
    "00c-raw-underhang": (
        "Normal vs underhang bearing faults (motor side)",
        [NORMAL,
         ("Underhang outer race 0 g", "underhang", "outer_race", 0),
         ("Underhang ball 0 g", "underhang", "ball_fault", 0),
         ("Underhang cage 0 g", "underhang", "cage_fault", 0)],
    ),
    "00d-raw-overhang": (
        "Normal vs overhang bearing faults (free end)",
        [NORMAL,
         ("Overhang outer race 0 g", "overhang", "outer_race", 0),
         ("Overhang ball 0 g", "overhang", "ball_fault", 0),
         ("Overhang cage 0 g", "overhang", "cage_fault", 0)],
    ),
}


def make_figure(index: pd.DataFrame, name: str, title: str, groups: list,
                target_hz: float, window_ms: float) -> tuple[Path, pd.DataFrame]:
    rows_sel = []
    for label, cls, sub, mass in groups:
        r = mf.pick_matched_speed(index, target_hz, cls, subclass=sub, mass_g=mass)
        rows_sel.append((label, cls, r))

    n = int(window_ms / 1000.0 * FS)
    t = np.arange(n) / FS * 1000.0
    data = {label: mf.load(r["path"], CHANNELS) for label, _, r in rows_sel}

    ncol = len(rows_sel)
    fig, axes = plt.subplots(len(CHANNELS), ncol, figsize=(3.4 * ncol + 1.2, 12.5),
                             sharex=True, squeeze=False)

    summary = []
    for ri, ch in enumerate(CHANNELS):
        seg = {}
        for label, _, _ in rows_sel:
            v = data[label][ch].to_numpy()[:n]
            seg[label] = v - v.mean()
        ymax = max(np.abs(v).max() for v in seg.values()) * 1.05
        ref = seg["Normal"]
        ref_p2p = float(ref.max() - ref.min())

        for ci, (label, cls, r) in enumerate(rows_sel):
            ax = axes[ri, ci]
            if cls != "normal":
                ax.plot(t, ref, color=style.REFERENCE, linewidth=0.5, zorder=1)
            ax.plot(t, seg[label], color=style.color(cls), linewidth=0.6, zorder=2)
            ax.set_ylim(-ymax, ymax)

            p2p = float(seg[label].max() - seg[label].min())
            ratio = p2p / ref_p2p
            summary.append({"figure": name, "group": label, "channel": ch,
                            "file": r["rel"], "p2p_g": round(p2p, 3),
                            "vs_normal": round(ratio, 2)})
            if cls != "normal":
                ax.annotate(f"{ratio:.2f}x", xy=(0.97, 0.92), xycoords="axes fraction",
                            ha="right", va="top", fontsize=8, color=style.INK)

            if ri == 0:
                rot = _rot(r)
                ax.set_title(f"{label}\n{rot:.2f} Hz ({rot * 60:.0f} rpm)",
                             fontsize=9.5, loc="left")
            if ci == 0:
                ax.set_ylabel(f"{ch}\n(g)", fontsize=9)
            if ri == len(CHANNELS) - 1:
                ax.set_xlabel("Time (ms)", fontsize=8.5)

    style.finish(
        fig,
        title,
        f"~{target_hz:.0f} Hz shaft · {window_ms:.0f} ms window · grey = Normal on the same channel · "
        "y shared within a row · number = peak-to-peak vs Normal · ONE file per group",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    path = OUT / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return path, pd.DataFrame(summary)


def main() -> int:
    ap = argparse.ArgumentParser(description="สำรวจสัญญาณดิบทุกช่อง แยก 4 รูป")
    ap.add_argument("--target-hz", type=float, default=30.0)
    ap.add_argument("--window-ms", type=float, default=67.0,
                    help="ความกว้างหน้าต่าง (ms) ค่าเริ่มต้นราว 2 รอบที่ 30 Hz")
    args = ap.parse_args()

    style.apply()
    OUT.mkdir(parents=True, exist_ok=True)
    index = mf.build_index()

    # ลบรูปรวม 36 แผงเดิมถ้ายังอยู่ ชุดนี้มาแทน
    old = OUT / "00-raw-all-channels.png"
    if old.exists():
        old.unlink()

    all_rows = []
    for name, (title, groups) in FIGURES.items():
        path, df = make_figure(index, name, title, groups, args.target_hz, args.window_ms)
        all_rows.append(df)
        piv = df.pivot(index="channel", columns="group", values="vs_normal").reindex(CHANNELS)
        piv = piv[[g[0] for g in groups]]
        print(f"\n=== {path.relative_to(repo_root())} ===")
        print(piv.to_string())

    csv = repo_root() / "data" / "processed" / "raw_channel_p2p.csv"
    csv.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(all_rows).to_csv(csv, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

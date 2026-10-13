"""วัดความสูงของพีคที่ 1× และอัตราส่วน 2×/1× ให้ครบทุกไฟล์

## ทำไมต้องมี

ตารางสองตารางในหัวข้อ "เลือกช่องเซ็นเซอร์ให้ตรงกับความเสียหาย" ของ `CLAUDE.md`
ระบุว่า **วัดจากคลาสละ 8–10 ไฟล์** ซึ่งน้อยเกินกว่าจะเป็นค่าของทั้งกลุ่ม
โดยเฉพาะเมื่อการกระจายภายในกลุ่มกว้างมาก

วัดใหม่ครบทุกไฟล์ในช่วงความเร็วเดียวกันแล้วพบว่า **ตัวเลขเดิมสูงเกินจริงทุกตัว**
และทุกตัวเอนไปทางที่ทำให้ผลดูชัดกว่าความจริง

| กลุ่ม (อัตราส่วน 2×/1× บน `o_tang`) | เดิม | วัดครบ |
|---|---:|---:|
| imbalance 35 g | 0.44 | 0.55 |
| horizontal-misalignment | 2.18 | 1.43 |
| vertical-misalignment | 5.36 | 3.86 |
| overhang bearing 0 g | 3.01 | 2.07 |

ทดสอบด้วยการสุ่ม 10 ไฟล์จากกลุ่มเดิม 200 ครั้ง **ค่าที่เคยรายงานไว้
อยู่ในช่วงที่ตัวอย่าง 10 ไฟล์ให้ได้ทั้งหมด** จึงอธิบายได้ว่าเป็นผลของตัวอย่างเล็ก
ไม่ใช่การคำนวณผิด

> **เป็นความผิดพลาดแบบเดียวกับตัวเลข 88 เท่าของช่อง `mic`** คือค่าของตัวอย่าง
> ถูกเขียนเหมือนเป็นค่าของทั้งกลุ่ม **ครั้งนี้ต่างตรงที่มีหลายตัวเลขพร้อมกัน
> และทุกตัวเอนไปทางเดียวกัน** ซึ่งเป็นรูปแบบที่ควรสงสัยว่าไฟล์ที่เลือก
> อาจไม่ได้สุ่มจริง แต่เป็นไฟล์ที่เห็นผลชัด

## สิ่งที่สคริปต์นี้รายงานต่างจากของเดิม

**รายงานช่วงการกระจายคู่กับค่ากลางเสมอ** เพราะกลุ่มเหล่านี้กระจายกว้างมาก
เช่น `h-misalignment` อยู่ระหว่าง 0.125 ถึง 4.897 คือกว้าง 39 เท่า
การรายงานค่ากลางอย่างเดียวจึงชวนให้เข้าใจว่าแยกกลุ่มได้ขาดกว่าความจริง

รัน:
    python src/features/check_harmonic_ratios.py
    python src/features/check_harmonic_ratios.py --lo 24 --hi 36
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda                      # noqa: E402
from src.features import spectral                  # noqa: E402
from src.paths import repo_root, sampling_rate     # noqa: E402

CHANNELS = ["u_axial", "u_radial", "u_tang", "o_axial", "o_radial", "o_tang"]

# (ชื่อที่แสดง, เงื่อนไขเลือกไฟล์)
GROUPS = [
    ("normal", dict(cls="normal")),
    ("imbalance 35 g", dict(cls="imbalance", mass_g=35)),
    ("horizontal-misalignment", dict(cls="horizontal-misalignment")),
    ("vertical-misalignment", dict(cls="vertical-misalignment")),
    ("underhang bearing 0 g", dict(cls="underhang", mass_g=0)),
    ("overhang bearing 0 g", dict(cls="overhang", mass_g=0)),
]


def measure(row, fs: float) -> dict[str, tuple[float, float]]:
    """คืน {ช่อง: (แอมพลิจูดที่ 1×, อัตราส่วน 2×/1×)} ของไฟล์เดียว"""
    df = mafaulda.load(row.path, channels=CHANNELS)
    out = {}
    for ch in CHANNELS:
        f, mag = spectral.spectrum(df[ch].to_numpy(), fs)
        _, a1 = spectral.peak_near(f, mag, row.spd)
        _, a2 = spectral.peak_near(f, mag, 2 * row.spd)
        out[ch] = (a1, a2 / a1 if a1 > 0 else np.nan)
    return out


def table(rows: list[str], title: str, head: list[str]) -> None:
    rows.append("")
    rows.append(title)
    rows.append("")
    rows.append("| " + " | ".join(head) + " |")
    rows.append("|---" * len(head) + "|")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lo", type=float, default=24.0, help="ความเร็วรอบต่ำสุด (Hz)")
    ap.add_argument("--hi", type=float, default=36.0, help="ความเร็วรอบสูงสุด (Hz)")
    ap.add_argument("--out", type=Path,
                    default=repo_root() / "experiments")
    a = ap.parse_args()

    fs = float(sampling_rate())
    idx = mafaulda.build_index()
    idx = idx.assign(spd=mafaulda.speed_hz(idx))
    sel = idx[(idx.spd >= a.lo) & (idx.spd <= a.hi)]

    stats: dict[str, dict[str, np.ndarray]] = {}
    for name, cond in GROUPS:
        g = sel
        for k, v in cond.items():
            g = g[g[k] == v]
        if g.empty:
            print(f"ข้าม {name} เพราะไม่พบไฟล์ในช่วงความเร็วที่กำหนด")
            continue
        per_file = [measure(r, fs) for r in g.itertuples()]
        stats[name] = {
            ch: np.array([[p[ch][0] for p in per_file],
                          [p[ch][1] for p in per_file]])
            for ch in CHANNELS
        }
        stats[name]["_n"] = len(g)
        print(f"วัดแล้ว {name}: {len(g)} ไฟล์")

    base = stats["normal"]
    out: list[str] = [
        f"# ความสูงของพีคที่ 1× และอัตราส่วน 2×/1× วัดครบทุกไฟล์",
        "",
        f"ช่วงความเร็วรอบ {a.lo:.0f}–{a.hi:.0f} Hz · "
        f"อ่านทุกไฟล์ในช่วงนี้ ไม่ได้สุ่มตัวอย่าง",
        "",
        "ตัวเลขเทียบเป็นเท่าของสภาวะปกติในช่องเดียวกัน และรายงานช่วงการกระจาย",
        "คู่กันเสมอ เพราะกลุ่มเหล่านี้กระจายกว้างมากจนค่ากลางอย่างเดียวชวนให้",
        "เข้าใจว่าแยกกลุ่มได้ขาดกว่าความจริง",
    ]

    for which, idx_row, label in ((0, 0, "ความสูงของพีคที่ 1×"),
                                  (1, 1, "อัตราส่วน 2×/1×")):
        table(out, f"## {label}",
              ["กลุ่ม", "ไฟล์"] + [f"`{c}`" for c in CHANNELS])
        for name in stats:
            s = stats[name]
            cells = []
            for ch in CHANNELS:
                med = float(np.nanmedian(s[ch][idx_row]))
                b = float(np.nanmedian(base[ch][idx_row]))
                cells.append("1.00" if name == "normal" else f"{med / b:.2f}")
            out.append(f"| {name} | {s['_n']} | " + " | ".join(cells) + " |")

        table(out, f"### ช่วงการกระจายของ{label} บน `o_tang` (ค่าดิบ)",
              ["กลุ่ม", "ไฟล์", "ต่ำสุด", "มัธยฐาน", "สูงสุด", "กว้างกี่เท่า"])
        for name in stats:
            v = stats[name]["o_tang"][idx_row]
            lo, med, hi = (float(np.nanmin(v)), float(np.nanmedian(v)),
                           float(np.nanmax(v)))
            out.append(f"| {name} | {stats[name]['_n']} | {lo:.3f} | {med:.3f} "
                       f"| {hi:.3f} | {hi / lo:.0f} |")

    a.out.mkdir(parents=True, exist_ok=True)
    path = a.out / "2026-10-13-harmonic-ratios-full.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"\nเขียนผลลง {path}")

    fig = draw(stats)
    print(f"เขียนรูปลง {fig}")
    return 0


def draw(stats) -> Path:
    """วาดการกระจายของอัตราส่วน 2×/1× ต่อกลุ่ม

    **รูปนี้จำเป็น** เพราะตารางรายงานค่ากลาง ซึ่งปิดบังความจริงว่าช่วงของ
    แต่ละกลุ่มซ้อนทับกันเป็นบริเวณกว้าง ถ้าเห็นแต่ตาราง ผู้อ่านจะเข้าใจว่า
    ตัวชี้วัดนี้แยกกลุ่มได้ขาด ซึ่งไม่จริง

    ใช้แกนลอการิทึม เพราะกลุ่มที่กว้างที่สุดกว้างถึง 341 เท่า
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.viz import style
    from src.viz.make_spectrum_figure import thai_font

    style.apply()
    font = thai_font()
    if font is None:
        raise SystemExit("ไม่พบฟอนต์ไทย — ป้ายกำกับจะเป็นสี่เหลี่ยมเปล่า")
    plt.rcParams["font.family"] = font

    names = list(stats)
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    rng = np.random.default_rng(0)
    base = float(np.nanmedian(stats["normal"]["o_tang"][1]))

    for i, name in enumerate(names):
        v = stats[name]["o_tang"][1]
        v = v[np.isfinite(v)]
        cls = next(c["cls"] for n, c in GROUPS if n == name)
        col = style.CLASS_COLORS.get(cls, style.INK_SOFT)
        ax.scatter(v, np.full(len(v), i) + rng.uniform(-0.17, 0.17, len(v)),
                   s=16, alpha=0.55, color=col, edgecolors="none", zorder=3)
        med = float(np.median(v))
        ax.plot([med, med], [i - 0.32, i + 0.32], color=style.INK, lw=2.2, zorder=4)
        ax.text(ax.get_xlim()[1], i, f"  {med / base:.2f}×", va="center",
                fontsize=11, color=style.INK)

    ax.axvline(base, color=style.MARKER, lw=1.0, ls="--", zorder=1)
    ax.set_xscale("log")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=11.5)
    ax.invert_yaxis()
    ax.set_xlabel("อัตราส่วนความสูงของพีคที่ 2× ต่อพีคที่ 1×  (แกนลอการิทึม)",
                  fontsize=12)
    ax.set_title("หนึ่งจุดคือหนึ่งไฟล์  ·  เส้นทึบคือค่ากลางของกลุ่ม  ·  "
                 "เส้นประคือค่ากลางของสภาวะปกติ", fontsize=12.5, loc="left", pad=10)
    fig.text(0.5, -0.04,
             "ช่วงของแต่ละกลุ่มซ้อนทับกันเป็นบริเวณกว้าง ตัวชี้วัดนี้จึงบอกแนวโน้ม"
             "ของกลุ่มได้ แต่ใช้ตัดสินไฟล์เดี่ยวไม่ได้",
             ha="center", fontsize=11, color=style.INK_SOFT)

    out = repo_root() / "reports/figures/harmonic-ratio-spread.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out


if __name__ == "__main__":
    raise SystemExit(main())

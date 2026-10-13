"""รูปประกอบหัวข้อ "ความถี่พื้นฐาน" ของโครงร่าง — พีคในสเปกตรัมคืออะไร

สร้างรูปเดียวที่ตอบสองคำถามพร้อมกัน

1. **พีคในสเปกตรัมหน้าตาอย่างไร** แผงบนอธิบายด้วยคำกำกับบนตัวกราฟเอง
2. **ความผิดปกติแต่ละชนิดดันพีคที่ตำแหน่งต่างกันจริงหรือไม่**
   สี่แผงล่างเทียบสภาวะปกติกับความผิดปกติสามกลุ่มในตารางของหัวข้อนั้น

## เหตุผลที่ใช้ช่อง `o_tang` ทั้งรูป

ช่องเดียวที่เห็น**ทั้งสามแถวของตาราง**ได้พร้อมกัน

| สภาวะ | สิ่งที่เห็นบน `o_tang` |
|---|---|
| ความไม่สมดุล | พีคที่ 1× สูงขึ้น 11.26 เท่าของสภาวะปกติ |
| การเยื้องศูนย์ | อัตราส่วน 2×/1× สูงขึ้น 2.18 ถึง 5.36 เท่า |
| ตลับลูกปืน | ไม่ดันพีคที่ฮาร์มอนิกใดเป็นพิเศษ |

⚠️ **ห้ามใช้ `u_radial`** ซึ่งเป็นช่องที่กราฟ EDA เดิมใช้ เพราะวัดแล้วพบว่า
**มองไม่เห็นการเยื้องศูนย์เลย** (อัตราส่วน 0.8–1.0 ทุกระดับ)
ถ้าวาดด้วยช่องนั้น รูปจะขัดกับตารางในเอกสาร

## คุมความเร็วรอบ

ทุกแผงเลือกไฟล์ที่ความเร็วรอบใกล้ค่าเป้าหมายที่สุด เพราะถ้าไม่คุม
สิ่งที่เห็นว่าต่างกันส่วนใหญ่จะเป็นผลของความเร็ว ไม่ใช่ของความเสียหาย
และแกน x เป็น**จำนวนเท่าของความเร็วรอบ** ไม่ใช่เฮิรตซ์ ซึ่งเป็นประเด็น
ที่หัวข้อนั้นอธิบายไว้พอดี

รัน:
    python src/viz/make_spectrum_figure.py
    python src/viz/make_spectrum_figure.py --target-hz 30 --out reports/figures
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda                      # noqa: E402
from src.features import spectral                  # noqa: E402
from src.paths import repo_root, sampling_rate     # noqa: E402
from src.viz import style                          # noqa: E402

CHANNEL = "o_tang"
N_HARM = 5          # วาดถึง 5× พอ เพราะเกินนั้นพลังงานน้อยจนอ่านไม่ออก
LO_CUT = 0.30       # ตัดต่ำกว่า 0.30× ทิ้ง ดูเหตุผลใน panel_spectrum()

# (ชื่อที่แสดง, cls, subclass, mass_g) — subclass/mass เป็น None คือไม่เจาะจง
PANELS = [
    ("สภาวะปกติ", "normal", None, None),
    ("ความไม่สมดุลของมวล 35 g", "imbalance", None, 35),
    ("การเยื้องศูนย์แนวดิ่ง 1.90 mm", "vertical-misalignment", "1.90mm", None),
    ("ตลับลูกปืนเสียหาย (รางนอก)", "underhang", "outer_race", 0),
]


def thai_font() -> str | None:
    """หาฟอนต์ไทยที่มีในเครื่อง

    ต้องตั้งให้ matplotlib เพราะฟอนต์ปริยายไม่มีสระและวรรณยุกต์ไทย
    ถ้าไม่ตั้งจะได้สี่เหลี่ยมเปล่าทั้งแผง **โดยไม่มี error ใดๆ**
    ซึ่งเป็นความผิดพลาดเงียบอีกแบบหนึ่ง
    """
    import matplotlib.font_manager as fm
    have = {f.name for f in fm.fontManager.ttflist}
    for want in ("TH Sarabun New", "TH SarabunPSK", "Leelawadee UI", "Tahoma"):
        if want in have:
            return want
    return None


def harmonic(order: np.ndarray, mag: np.ndarray, k: float, half: float = 0.04) -> float:
    """แอมพลิจูดสูงสุดในหน้าต่างแคบรอบฮาร์มอนิกที่ k

    ต้องมีหน้าต่างเผื่อ เพราะความเร็วรอบแกว่งเล็กน้อยระหว่างบันทึก
    พีคจึงไม่ได้ตกที่จำนวนเต็มพอดีเสมอไป
    """
    m = (order >= k - half) & (order <= k + half)
    return float(mag[m].max()) if m.any() else 0.0


def panel_spectrum(row, fs: float):
    """คืน (แกน x เป็นจำนวนเท่าของความเร็วรอบ, แอมพลิจูด, ความเร็วรอบ)"""
    x = mafaulda.load(row.path, channels=[CHANNEL])[CHANNEL].to_numpy()
    rot = float(mafaulda.speed_hz(row.to_frame().T).iloc[0])
    freqs, mag = spectral.spectrum(x, fs)
    # ตัดทุกอย่างใต้ LO_CUT ทิ้ง เพราะเป็น drift ความถี่ต่ำของฐานเครื่อง
    # ไม่ใช่ฮาร์มอนิกของการหมุน และสูงกว่าพีคจริงหลายเท่าในบางสภาวะ
    # (วัดได้ว่าการเยื้องศูนย์แนวดิ่งมี drift 4.80 ขณะที่พีคที่ 1× มีแค่ 0.12)
    keep = (freqs >= LO_CUT * rot) & (freqs <= (N_HARM + 0.6) * rot)
    return freqs[keep] / rot, mag[keep], rot


def build(target_hz: float, out_dir: Path) -> Path:
    style.apply()
    font = thai_font()
    if font is None:
        raise SystemExit("ไม่พบฟอนต์ไทยในเครื่อง — ป้ายกำกับจะเป็นสี่เหลี่ยมเปล่า")
    plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False

    fs = float(sampling_rate())
    idx = mafaulda.build_index()

    picked = []
    for label, cls, sub, mass in PANELS:
        row = mafaulda.pick_matched_speed(idx, target_hz, cls, sub, mass)
        picked.append((label, cls, row))

    data = [(label, cls) + panel_spectrum(row, fs) for label, cls, row in picked]
    ymax = max(float(mag.max()) for _, _, _, mag, _ in data) * 1.18

    fig = plt.figure(figsize=(9.6, 8.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 1, 1], hspace=0.42, wspace=0.18)

    # ---------------------------------------------------- แผงบน: อธิบายศัพท์
    ax = fig.add_subplot(gs[0, :])
    label0, cls0, order0, mag0, rot0 = data[1]      # ใช้ความไม่สมดุล เพราะพีคชัดที่สุด
    ax.plot(order0, mag0, lw=1.0, color=style.CLASS_COLORS[cls0])
    for k in range(1, N_HARM + 1):
        ax.axvline(k, color=style.MARKER, lw=0.7, ls=":", zorder=0)
    ax.set_xlim(LO_CUT, N_HARM + 0.6)
    ax.set_ylim(0, ymax)

    h1 = harmonic(order0, mag0, 1)
    h2 = harmonic(order0, mag0, 2)
    ax.annotate("พีค คือยอดแหลมที่โผล่ขึ้นมาจากพื้น\nแปลว่าพลังงานกระจุกอยู่ที่ความถี่นั้น",
                xy=(1.0, h1), xytext=(1.6, ymax * 0.80),
                fontsize=12.5, color=style.INK,
                arrowprops=dict(arrowstyle="->", color=style.INK_SOFT, lw=1.0))
    ax.annotate("ฮาร์มอนิก คือพีคที่ความถี่\nเป็นจำนวนเท่าของความเร็วรอบ",
                xy=(2.0, h2), xytext=(2.6, ymax * 0.50),
                fontsize=12.5, color=style.INK,
                arrowprops=dict(arrowstyle="->", color=style.INK_SOFT, lw=1.0))
    # ชี้ไปที่ตำแหน่งที่ไม่มีพีคจริงๆ จึงจะสื่อว่า "พื้น" คืออะไร
    floor_x = 3.5
    ax.annotate("ระดับพื้น คือส่วนที่ไม่มีพีค",
                xy=(floor_x, harmonic(order0, mag0, floor_x, half=0.1)),
                xytext=(3.55, ymax * 0.25),
                fontsize=12.5, color=style.INK_SOFT,
                arrowprops=dict(arrowstyle="->", color=style.INK_SOFT, lw=1.0))
    ax.set_title(f"สเปกตรัมคือการกระจายพลังงานของการสั่นตามความถี่  "
                 f"(ตัวอย่างจาก{label0} ที่ {rot0:.1f} Hz)",
                 fontsize=13.5, loc="left", pad=10)
    ax.set_ylabel("แอมพลิจูด (g)", fontsize=12)
    ax.set_xticks(range(1, N_HARM + 1))
    ax.set_xticklabels([f"{k}×" for k in range(1, N_HARM + 1)], fontsize=12)
    ax.tick_params(labelsize=11)

    # ---------------------------------------------------- สี่แผงล่าง: เทียบสภาวะ
    for n, (label, cls, order, mag, rot) in enumerate(data):
        ax = fig.add_subplot(gs[1 + n // 2, n % 2])
        ax.plot(order, mag, lw=0.9, color=style.CLASS_COLORS[cls])
        for k in range(1, N_HARM + 1):
            ax.axvline(k, color=style.MARKER, lw=0.6, ls=":", zorder=0)
        ax.set_xlim(LO_CUT, N_HARM + 0.6)
        ax.set_ylim(0, ymax)
        # ใส่ตัวเลขกำกับ เพื่อให้รูปสื่อสารสิ่งเดียวกับตารางในเนื้อหา
        # ไม่ใช่ให้ผู้อ่านกะด้วยสายตาว่าพีคไหนสูงกว่า
        a1, a2 = harmonic(order, mag, 1), harmonic(order, mag, 2)
        ratio = a2 / a1 if a1 > 0 else float("nan")
        ax.text(0.975, 0.93, f"พีคที่ 1× = {a1:.3f} g\n2×/1× = {ratio:.2f}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=11, color=style.INK_SOFT, linespacing=1.5)
        ax.set_title(f"{label}  ·  {rot:.1f} Hz", fontsize=12, loc="left", pad=6)
        ax.set_xticks(range(1, N_HARM + 1))
        ax.set_xticklabels([f"{k}×" for k in range(1, N_HARM + 1)], fontsize=11)
        ax.tick_params(labelsize=10)
        if n % 2 == 0:
            ax.set_ylabel("แอมพลิจูด (g)", fontsize=11)
        if n >= 2:
            ax.set_xlabel("ความถี่ เป็นจำนวนเท่าของความเร็วรอบ", fontsize=11)

    fig.suptitle("ตำแหน่งของพีคในสเปกตรัม บอกได้ว่าเครื่องจักรผิดปกติด้วยสาเหตุใด",
                 fontsize=15, y=0.985)
    fig.text(0.5, 0.012,
             f"ช่องสัญญาณ {CHANNEL} (ตลับลูกปืนด้านนอกโรเตอร์ ตามทิศการหมุน)  ·  "
             f"ชุดข้อมูล MAFAULDA  ·  คุมความเร็วรอบไว้ใกล้ {target_hz:.0f} Hz ทุกแผง",
             ha="center", fontsize=10.5, color=style.INK_SOFT)

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "spectrum-peaks.png"
    fig.savefig(out, dpi=170)
    plt.close(fig)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target-hz", type=float, default=30.0)
    ap.add_argument("--out", type=Path, default=repo_root() / "reports/figures")
    a = ap.parse_args()

    out = build(a.target_hz, a.out)
    print(f"เขียนรูปลง {out}")
    print(f"ใช้ฟอนต์ {plt.rcParams['font.family']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

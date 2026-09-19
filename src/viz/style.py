"""สไตล์กลางของกราฟทุกใบในโปรเจกต์

จุดประสงค์คือให้กราฟทุกใบใน `reports/` ดูเป็นชุดเดียวกัน และให้สีของแต่ละคลาส
**คงที่ตลอดทั้งรายงาน** ถ้ากราฟใบหนึ่ง imbalance เป็นสีส้ม อีกใบต้องส้มเหมือนกัน
ไม่งั้นคนอ่านต้องกลับไปดู legend ใหม่ทุกใบ

จานสีผ่านการตรวจ colour-vision-deficiency แล้ว (worst adjacent CVD ΔE 9.1,
normal-vision ΔE 19.6) แต่สามสีคือ aqua, yellow, magenta มี contrast ต่อพื้นหลัง
ต่ำกว่า 3:1 จึง**ห้ามใช้สีอย่างเดียวในการบอกว่าเส้นไหนคืออะไร** ทุกแผงต้องมี
ข้อความกำกับเสมอ ซึ่งเป็นเหตุผลที่กราฟในโปรเจกต์นี้ใช้ small multiple
(หนึ่งคลาสต่อหนึ่งแผง มีหัวแผงบอกชื่อ) แทนการเอาทุกคลาสมาซ้อนกันในแผงเดียว
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e3e2de"
REFERENCE = "#b8b7b2"   # เส้นอ้างอิง normal ที่วาดไว้ข้างหลัง
MARKER = "#52514e"      # เส้นประบอกตำแหน่งความถี่ที่คาดหวัง

# ลำดับสีคงที่ ห้ามวนใช้ซ้ำ ห้ามสลับลำดับ
CLASS_COLORS = {
    "normal": "#2a78d6",                   # blue
    "imbalance": "#eb6834",                # orange
    "horizontal-misalignment": "#1baf7a",  # aqua
    "vertical-misalignment": "#eda100",    # yellow
    "underhang": "#e87ba4",                # magenta
    "overhang": "#008300",                 # green
}


def apply() -> None:
    """ตั้งค่า matplotlib ทั้งโปรเซส เรียกครั้งเดียวตอนเริ่มสคริปต์"""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 140,
        "savefig.bbox": "tight",

        # แกนและเส้นกริดต้องถอยไปอยู่ข้างหลัง ไม่แย่งสายตากับข้อมูล
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,

        "axes.labelcolor": INK_SOFT,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
        "legend.frameon": False,

        "lines.linewidth": 1.0,
        "lines.solid_capstyle": "round",

        # ใช้ label ภาษาอังกฤษบนกราฟทั้งหมด เพราะฟอนต์เริ่มต้นของ matplotlib
        # ไม่มีอักษรไทย ถ้าใส่ไทยจะกลายเป็นสี่เหลี่ยมเปล่า และบน Raspberry Pi
        # ก็ไม่มีฟอนต์ไทยติดมาด้วย คำอธิบายภาษาไทยอยู่ในไฟล์ .md แทน
        "font.family": "DejaVu Sans",
    })


def color(cls: str) -> str:
    return CLASS_COLORS.get(cls, INK_SOFT)


def annotate_lines(ax, marks: dict[str, float], ymax: float | None = None) -> None:
    """วาดเส้นประแนวตั้งบอกตำแหน่งความถี่ที่ทฤษฎีบอกว่าควรเจอพีค

    การวาดเส้นพวกนี้คือหัวใจของการอ่านกราฟ ถ้าไม่มีก็ได้แค่ "เห็นพีคเยอะดี"
    แต่บอกไม่ได้ว่าพีคนั้นคือความเสียหายชนิดไหน
    """
    lim = ax.get_xlim()
    for name, f in marks.items():
        if not (lim[0] <= f <= lim[1]):
            continue
        ax.axvline(f, color=MARKER, linestyle=(0, (3, 3)), linewidth=0.8, alpha=0.7, zorder=1)
        ax.annotate(
            name,
            xy=(f, 1.0), xycoords=("data", "axes fraction"),
            xytext=(2, -2), textcoords="offset points",
            fontsize=7, color=MARKER, va="top", ha="left",
        )


def finish(fig, title: str, subtitle: str = "") -> None:
    """ใส่หัวเรื่องให้รูป — หัวเรื่องคือสิ่งที่บอกว่ารูปนี้ต้องการให้เห็นอะไร"""
    fig.suptitle(title, fontsize=13, fontweight="bold", color=INK, x=0.01, ha="left")
    if subtitle:
        fig.text(0.01, 1.0, subtitle, fontsize=8.5, color=INK_SOFT, ha="left", va="bottom")


__all__ = ["apply", "color", "annotate_lines", "finish",
           "CLASS_COLORS", "SURFACE", "INK", "INK_SOFT", "GRID", "REFERENCE", "MARKER"]

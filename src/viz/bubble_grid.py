"""Bubble plot ของทั้ง dataset — เห็นแนวโน้มทั้งสองแกนพร้อมกันในภาพเดียว

`browse_waveforms.py` ให้ดูทีละจุด ต้องเลื่อนแถบไปเรื่อยๆ แล้วจำเอาเองว่าค่าที่มุมขวาบน
เปลี่ยนไปยังไง โปรแกรมนี้เอาค่านั้นของ**ทุกไฟล์**มาวางในภาพเดียว

    แกน X   มวลถ่วง (g) หรือระยะเยื้องศูนย์ (mm) แล้วแต่คลาส
    แกน Y   ความเร็วรอบ (Hz)
    ขนาดวง  peak-to-peak เทียบกับ normal ที่ความเร็วเดียวกัน
    สีวง    ค่าเดียวกันในสเกล log — แดง = แรงกว่า normal, น้ำเงิน = เบากว่า

**แถบ `Normal` ทางซ้ายคือพื้นความคลาดเคลื่อน** เป็น normal ทั้ง 49 ไฟล์เทียบกับ
เส้นฐานของตัวเอง ค่าจึงวนอยู่รอบ 1.0 ส่วนที่มันกระจายออกจาก 1.0 คือความแปรปรวน
ที่เครื่อง**ปกติ**สร้างขึ้นเองจากรอบการบันทึกและการวัด **ความเสียหายจะน่าเชื่อถือ
ก็ต่อเมื่อดันค่าออกไปไกลกว่าแถบนี้** ถ้าวงในกราฟหลักโตพอๆ กับวงในแถบนี้
แปลว่ายังแยกจากเครื่องปกติไม่ได้

แถบนี้แยกแกนออกมาต่างหาก **ไม่เอาไปต่อท้ายแกน X เดียวกัน** เพราะ x = 0 ของคลาส
bearing หมายถึง "มวลถ่วง 0 กรัม" ซึ่งเป็นตลับลูกปืนที่เสียแล้ว ไม่ใช่เครื่องปกติ
ถ้าวางไว้ติดกันบนแกนเดียวจะอ่านสลับกันทันที ขนาดวงของทั้งสองแกนคิดจากตัวหารเดียวกัน
จึงเทียบข้ามแกนได้ตรงๆ

**ทำไมต้องใส่สีด้วยทั้งที่ขนาดบอกอยู่แล้ว** เพราะขนาดวงกลมบอกค่าที่**น้อยกว่า 1**
ไม่ได้ วงที่เล็กจิ๋วแยกไม่ออกระหว่าง "เบากว่า normal 5 เท่า" กับ "เท่ากับ normal"
ทั้งที่สองอย่างนี้มีความหมายต่างกันสิ้นเชิง (h-misalign ทำให้ `o_axial` เบาลง 3 เท่า
ซึ่งเป็นลายเซ็นที่ชัดที่สุดอันหนึ่ง) สีจึงเป็นตัวบอกทิศทาง ส่วนขนาดบอกขนาด
การเข้ารหัสซ้ำสองทางแบบนี้ยังช่วยตอนวงซ้อนกันด้วย

**สเกลของสีคงที่เสมอ** (0.1× ถึง 100×) จึงเทียบข้ามคลาสและข้ามช่องได้ตรงๆ
ส่วน**ขนาดวงปรับตามค่ามากสุดของภาพที่กำลังดู** จึงเทียบขนาดข้ามภาพไม่ได้
ค่ามากสุดของภาพนั้นพิมพ์ไว้บนหัวเรื่องแล้ว

ปุ่มเลือกคลาสและช่องทางซ้าย **คลิกที่ไหนก็ได้ในแถว** ไม่ต้องเล็งวงกลม

ต้องมีตาราง `data/processed/p2p_grid.csv` ก่อน สร้างด้วย
    python src/features/p2p_grid.py

รัน:
    python src/viz/bubble_grid.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from matplotlib.widgets import RadioButtons

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import processed_dir  # noqa: E402
from src.viz import style  # noqa: E402
from src.viz.browse_waveforms import CATEGORIES, SIGNATURES, STATUS_COLOR  # noqa: E402
from src.viz.explore_raw_channels import CHANNELS  # noqa: E402
from src.viz.widgets import row_clickable  # noqa: E402

# ช่วงสีคงที่ ไม่ขึ้นกับภาพที่กำลังดู เพื่อให้เทียบข้ามคลาสได้
COLOR_LO, COLOR_HI = 0.1, 100.0
AREA_MIN, AREA_MAX = 14.0, 460.0        # ขนาดวงเป็น point^2
RADIO_SIZE = 110.0                      # ขนาดวงกลมของปุ่มเรดิโอ (point^2)

# feature ที่วัด "ความแรง" เหมือน peak-to-peak จึงอ่านจากกราฟนี้ได้ตรงๆ
# ตัวอื่น (อัตราส่วน สัดส่วนพลังงาน kurtosis) เป็นคนละปริมาณ ดูจากกราฟนี้ไม่ได้
AMPLITUDE_LIKE = {"rms", "env_floor"}
SIZE_LEGEND_FRAC = (0.15, 0.5, 1.0)     # สัดส่วนของค่ามากสุด ที่เอามาทำตัวอย่างขนาด

# normal ที่ใช้เป็นฐานเทียบมีไฟล์เดียวต่อความเร็ว ค่าจึงกระเพื่อม
# ใช้มัธยฐานเคลื่อนที่ 3 จุด (กว้างราว 3 Hz) ให้เส้นฐานนิ่งก่อนเอาไปหาร
REF_SMOOTH = 3


def level_values(tab: pd.DataFrame, cat) -> pd.Series:
    """ค่าที่จะไปอยู่บนแกน X ของคลาสนี้ — มวลถ่วง (g) หรือระยะเยื้องศูนย์ (mm)"""
    return tab["severity"] if cat.unit == "mm" else tab["mass_g"]


class BubbleGrid:
    def __init__(self, tab: pd.DataFrame):
        self.tab = tab
        self.cat = CATEGORIES[0]
        self.channel = SIGNATURES[self.cat.label].channel
        self.ref = self._reference_curves(tab)
        self.points = pd.DataFrame()
        self.ref_points = pd.DataFrame()
        self._mute = False          # กันไม่ให้ callback ของปุ่มช่องวาดซ้ำ
        self._build()
        self._redraw()

    # ---------- ข้อมูล ----------

    def _reference_curves(self, tab: pd.DataFrame) -> dict[str, tuple]:
        """เส้นฐาน normal ของแต่ละช่อง เป็นฟังก์ชันของความเร็วรอบ"""
        n = tab[tab["cls"] == "normal"].sort_values("rot_hz_used")
        out = {}
        for ch in CHANNELS:
            y = n[f"p2p_{ch}"].rolling(REF_SMOOTH, center=True, min_periods=1).median()
            out[ch] = (n["rot_hz_used"].to_numpy(), y.to_numpy())
        return out

    def _ratio(self, sel: pd.DataFrame) -> np.ndarray:
        x, y = self.ref[self.channel]
        base = np.interp(sel["rot_hz_used"].to_numpy(), x, y)
        return sel[f"p2p_{self.channel}"].to_numpy() / base

    def _select(self) -> pd.DataFrame:
        sel = self.tab[self.tab["cls"] == self.cat.cls]
        if self.cat.subclass is not None:
            sel = sel[sel["subclass"] == self.cat.subclass]
        return pd.DataFrame({
            "x": level_values(sel, self.cat).to_numpy(),
            "y": sel["rot_hz_used"].to_numpy(),
            "ratio": self._ratio(sel),
            "rel": sel["rel"].to_numpy(),
        }).dropna()

    def _select_normal(self) -> pd.DataFrame:
        """normal 49 ไฟล์ เทียบกับเส้นฐานของตัวเอง

        **นี่คือพื้นความคลาดเคลื่อน** ค่าที่ได้ควรวนอยู่รอบ 1.0 ส่วนที่มันกระจาย
        ออกจาก 1.0 ไปเท่าไร คือขนาดของความแปรปรวนที่เครื่อง**ปกติ**สร้างขึ้นเอง
        ความเสียหายจะน่าเชื่อถือก็ต่อเมื่อดันค่าออกไปไกลกว่านี้
        """
        sel = self.tab[self.tab["cls"] == "normal"]
        return pd.DataFrame({
            "x": np.full(len(sel), 0.5),
            "y": sel["rot_hz_used"].to_numpy(),
            "ratio": self._ratio(sel),
            "rel": sel["rel"].to_numpy(),
        }).dropna()

    # ---------- หน้าตา ----------

    def _build(self) -> None:
        self.fig = plt.figure(figsize=(12.6, 8.6))
        if self.fig.canvas.manager is not None:
            self.fig.canvas.manager.set_window_title("MAFAULDA bubble grid")

        # ⚠️ กับดักคลาสสิกของ matplotlib: CallbackRegistry เก็บ callback ที่เป็น
        # bound method ไว้เป็น **weak reference** ถ้าไม่มีใครถืออ็อบเจกต์นี้ไว้
        # Python จะเก็บกวาดมันทิ้งทันทีที่ __init__ คืนค่า แล้ว callback ทุกตัวก็ตาย
        # เงียบๆ อาการที่เห็นคือ **ปุ่มติ๊กได้แต่กราฟไม่อัปเดต** เพราะตัว widget เอง
        # ยังมีชีวิตอยู่ ผูกตัวเองไว้กับ figure ซึ่ง pyplot ถือไว้ให้ตลอดอายุหน้าต่าง
        self.fig._edge_pdm_app = self

        self.norm = TwoSlopeNorm(vmin=np.log10(COLOR_LO), vcenter=0.0,
                                 vmax=np.log10(COLOR_HI))

        # แถบ normal แยกออกมาต่างหาก ไม่เอาไปวางบนแกน X เดียวกับความรุนแรง
        # เพราะ x = 0 ของคลาส bearing คือ "มวลถ่วง 0 กรัม" ซึ่งเป็นตลับลูกปืนที่เสีย
        # แล้ว ไม่ใช่เครื่องปกติ ถ้าเอา normal ไปต่อท้ายแกนเดียวกันจะอ่านสลับกันทันที
        self.ax_ref = self.fig.add_axes((0.225, 0.095, 0.052, 0.755))
        self.ax_ref.set_ylabel("Shaft speed (Hz)")
        self.ax_ref.set_xlim(0, 1)
        self.ax_ref.set_xticks([0.5])
        self.ax_ref.set_xticklabels(["Normal"], fontsize=9)

        self.ax = self.fig.add_axes((0.310, 0.095, 0.540, 0.755), sharey=self.ax_ref)
        self.ax.tick_params(labelleft=False)

        scatter_kw = dict(cmap="RdBu_r", norm=self.norm, edgecolors=style.INK,
                          linewidths=0.4, alpha=0.85, zorder=3)
        self.scat = self.ax.scatter([], [], c=[], **scatter_kw)
        self.scat_ref = self.ax_ref.scatter([], [], c=[], **scatter_kw)

        cax = self.fig.add_axes((0.875, 0.095, 0.016, 0.755))
        cb = self.fig.colorbar(self.scat, cax=cax)
        cb.set_label("peak-to-peak vs Normal  (log scale)", fontsize=8.5)
        ticks = [0.1, 0.25, 0.5, 1, 2, 5, 10, 25, 100]
        cb.set_ticks([np.log10(t) for t in ticks])
        cb.set_ticklabels([f"{t:g}x" for t in ticks])
        cb.ax.tick_params(labelsize=8)
        cb.outline.set_visible(False)

        ax_cls = self.fig.add_axes((0.012, 0.545, 0.175, 0.325))
        ax_cls.set_title("Fault class", fontsize=9, loc="left", pad=6)
        ax_ch = self.fig.add_axes((0.012, 0.300, 0.175, 0.210))
        ax_ch.set_title("Sensor channel", fontsize=9, loc="left", pad=6)
        self.ax_size = self.fig.add_axes((0.012, 0.105, 0.175, 0.150))
        self.ax_size.set_title("Bubble size", fontsize=9, loc="left", pad=6)
        self.ax_size.set_xlim(0, 1)
        self.ax_size.set_ylim(0, 1)
        for a in (ax_cls, ax_ch, self.ax_size):
            a.set_facecolor(style.SURFACE)
            a.grid(False)
            a.set_xticks([])
            a.set_yticks([])
            for s in a.spines.values():
                s.set_visible(False)

        self.radio_cls = RadioButtons(ax_cls, [c.label for c in CATEGORIES], active=0,
                                      radio_props={"s": RADIO_SIZE})
        self.radio_cls.on_clicked(self._on_class)
        self.radio_ch = RadioButtons(ax_ch, list(CHANNELS),
                                     active=CHANNELS.index(self.channel),
                                     radio_props={"s": RADIO_SIZE})
        self.radio_ch.on_clicked(self._on_channel)
        for r in (self.radio_cls, self.radio_ch):
            for lbl in r.labels:
                lbl.set_fontsize(9)
            # วงกลมค่าเริ่มต้นโตแค่ 7 พิกเซล กดยากมาก จึงรับคลิกทั้งแถว
            row_clickable(r)

        self.t1 = self.fig.text(0.225, 0.975, "", fontsize=12.5, fontweight="bold",
                                color=style.INK, va="top")
        self.t2 = self.fig.text(0.225, 0.942, "", fontsize=8,
                                color=style.INK_SOFT, va="top")
        self.t3 = self.fig.text(0.225, 0.917, "", fontsize=8, va="top")
        self.pick_txt = self.fig.text(0.012, 0.072, "", fontsize=8,
                                      color=style.INK_SOFT, va="top")
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    # ---------- การตอบสนอง ----------

    def _on_class(self, label: str) -> None:
        self.cat = next(c for c in CATEGORIES if c.label == label)
        # ย้ายไปช่องที่เป็นลายเซ็นของคลาสใหม่ให้เลย เพราะเป็นช่องที่ควรดูก่อน
        # ตั้งปุ่มเองแล้วปิดเสียง callback ไว้ ไม่งั้นจะวาดสองรอบ
        sig = SIGNATURES[self.cat.label]
        if sig.status != "none" and self.radio_ch.value_selected != sig.channel:
            self.channel = sig.channel
            self._mute = True
            self.radio_ch.set_active(CHANNELS.index(sig.channel))
            self._mute = False
        self._redraw()

    def _on_channel(self, label: str) -> None:
        if self._mute:
            return
        self.channel = label
        self._redraw()

    def _on_click(self, event) -> None:
        """คลิกที่วงไหน บอกว่าไฟล์ไหนและค่าเท่าไร ใช้ได้ทั้งแถบ normal และกราฟหลัก"""
        if event.inaxes is self.ax:
            ax, pts = self.ax, self.points
        elif event.inaxes is self.ax_ref:
            ax, pts = self.ax_ref, self.ref_points
        else:
            return
        if pts.empty:
            return
        xr = np.ptp(ax.get_xlim()) or 1.0
        yr = np.ptp(ax.get_ylim()) or 1.0
        d = (((pts["x"] - event.xdata) / xr) ** 2
             + ((pts["y"] - event.ydata) / yr) ** 2)
        p = pts.iloc[int(d.idxmin())]
        self.pick_txt.set_text(f"clicked:\n{p['rel']}\n{p['ratio']:.2f}x Normal")
        self.fig.canvas.draw_idle()

    # ---------- การวาด ----------

    def _draw_bubbles(self, scat, p: pd.DataFrame, top: float) -> None:
        """พื้นที่วงแปรผันตรงกับค่า (ไม่ใช่รัศมี) เพราะสายตาคนอ่านพื้นที่ ไม่ใช่รัศมี

        ทั้งสองแกนใช้ ``top`` ตัวเดียวกัน ขนาดวงในแถบ normal จึงเทียบกับกราฟหลัก
        ได้ตรงๆ ถ้าแยกกันคิด วงของ normal จะโตเท่าวงที่ใหญ่ที่สุดของคลาสที่เสีย
        ซึ่งจะอ่านผิดทันที
        """
        scat.set_offsets(np.c_[p["x"], p["y"]])
        scat.set_array(np.log10(p["ratio"].clip(lower=COLOR_LO / 10)))
        scat.set_sizes(AREA_MIN + (AREA_MAX - AREA_MIN)
                       * (p["ratio"] / top).clip(lower=0))

    def _redraw(self) -> None:
        p = self._select()
        ref = self._select_normal()
        self.points = p.reset_index(drop=True)
        self.ref_points = ref.reset_index(drop=True)
        sig = SIGNATURES[self.cat.label]
        top = max(float(p["ratio"].max()) if len(p) else 1.0,
                  float(ref["ratio"].max()) if len(ref) else 1.0)

        self._draw_bubbles(self.scat, p, top)
        self._draw_bubbles(self.scat_ref, ref, top)

        levels = sorted(p["x"].unique())
        pad = (max(levels) - min(levels)) * 0.12 or 1.0
        self.ax.set_xlim(min(levels) - pad, max(levels) + pad)
        self.ax_ref.set_ylim(10, 64)
        self.ax.set_xticks(levels)
        self.ax.set_xlabel("Added mass (g)" if self.cat.unit == "g"
                           else "Misalignment offset (mm)")

        self._size_legend(top)
        self.t1.set_text(f"{self.cat.label}  ·  {self.channel}")
        lo, hi = ref["ratio"].min(), ref["ratio"].max()
        self.t2.set_text(
            f"{len(p)} files   |   bubble area and colour = median peak-to-peak vs "
            f"Normal at the same speed   |   largest here: {top:.2f}x   |   "
            f"Normal strip spans {lo:.2f}-{hi:.2f}x = how much a healthy machine "
            f"varies on its own")
        if sig.status == "none":
            self.t3.set_text("[none] no verified signature for this fault")
        else:
            mark = "<-- that channel" if self.channel == sig.channel else ""
            # ⚠️ วงกลมในกราฟนี้คือ peak-to-peak เสมอ ซึ่งเป็น **คนละปริมาณ**
            # กับลายเซ็นเกือบทุกตัว misalignment ไม่ได้ทำให้เครื่องสั่นแรงขึ้น
            # แต่ย้ายพลังงานจาก 1x ไป 2x ดังนั้น p2p แทบไม่ขยับขณะที่ r21 พุ่ง
            # ถ้าไม่เขียนกำกับไว้ คนอ่านจะสรุปว่าลายเซ็นใช้ไม่ได้ทั้งที่ดูผิดปริมาณ
            note = ("" if sig.feature in AMPLITUDE_LIKE else
                    "   |   bubbles show peak-to-peak, NOT this feature")
            self.t3.set_text(f"signature: {sig.channel}.{sig.feature}  "
                             f"({sig.expected})   {mark}{note}")
        self.t3.set_color(STATUS_COLOR[sig.status])
        self.pick_txt.set_text("")
        self.fig.canvas.draw_idle()

    def _size_legend(self, top: float) -> None:
        """วงตัวอย่างสามขนาด บอกว่าขนาดเท่านี้หมายถึงกี่เท่าในภาพที่กำลังดู"""
        self.ax_size.clear()
        self.ax_size.set_xlim(0, 1)
        self.ax_size.set_ylim(0, 1)
        self.ax_size.set_xticks([])
        self.ax_size.set_yticks([])
        self.ax_size.grid(False)
        ys = (0.80, 0.48, 0.16)
        for frac, y in zip(SIZE_LEGEND_FRAC, ys):
            area = AREA_MIN + (AREA_MAX - AREA_MIN) * frac
            self.ax_size.scatter([0.22], [y], s=area, facecolor="none",
                                 edgecolor=style.INK_SOFT, linewidths=0.7)
            self.ax_size.text(0.52, y, f"{top * frac:.2f}x", fontsize=8,
                              va="center", color=style.INK_SOFT)


def main() -> int:
    argparse.ArgumentParser(description="bubble plot ของ peak-to-peak ทั้ง dataset"
                            ).parse_args()

    cache = processed_dir() / "p2p_grid.csv"
    if not cache.is_file():
        print(f"ยังไม่มี {cache}\nสร้างก่อนด้วย  python src/features/p2p_grid.py",
              file=sys.stderr)
        return 1
    if plt.get_backend().lower() == "agg":
        print("matplotlib ใช้ backend 'agg' ซึ่งเปิดหน้าต่างไม่ได้ "
              "ต้องรันบนเครื่องที่มีจอ", file=sys.stderr)
        return 1

    style.apply()
    tab = pd.read_csv(cache, keep_default_na=False, na_values=[""])
    tab["severity"] = pd.to_numeric(tab["severity"], errors="coerce")
    app = BubbleGrid(tab)      # ต้องเก็บตัวแปรไว้ ดูคำอธิบายใน _build
    plt.show()
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

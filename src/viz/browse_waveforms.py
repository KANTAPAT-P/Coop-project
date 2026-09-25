"""โปรแกรมเลื่อนดูสัญญาณดิบ — เปลี่ยนความเร็วรอบและความรุนแรงแล้วดูกราฟเปลี่ยนตาม

รูป 00a–00d ใน `reports/eda/` ตรึงความเร็วไว้ที่ ~30 Hz และตรึงความรุนแรงไว้ค่าเดียว
(imbalance 35 g, misalign ค่ามากสุด, bearing 0 g) จึงตอบได้แค่ว่า "ที่จุดนั้นหน้าตาเป็นยังไง"
แต่ตอบไม่ได้ว่า **"ถ้าหมุนเร็วขึ้น หรือถ่วงหนักขึ้น กราฟเปลี่ยนไปทางไหน"**

โปรแกรมนี้เปิดหน้าต่างที่มีแถบเลื่อนสองแถบ
    แถบบน   ความเร็วรอบ 12–62 Hz
    แถบล่าง  ความรุนแรง — มวลถ่วง (g) หรือระยะเยื้องศูนย์ (mm) แล้วแต่หมวดที่เลือก
และปุ่มเลือกหมวดทางซ้าย 9 หมวด (imbalance, misalign 2 แบบ, bearing 2 ฝั่ง × 3 ชนิด)
หน้าจอแสดง 6 ช่องเซ็นเซอร์ซ้อนกันเหมือนรูป 00a–00d โดยมี normal
ที่**ความเร็วเดียวกัน**เป็นเส้นเทาอยู่ข้างหลังทุกแผง

**แถบลายเซ็น** บรรทัดที่สามของหัวเรื่องบอกว่าหมวดที่เลือกอยู่ใช้**ช่องไหนเป็นตัววัด**
และแผงของช่องนั้นจะถูกไฮไลต์พื้นหลังพร้อมเขียนกำกับว่าใช้ feature ตัวไหน
ตัวเลข `this file: N.NNx` คือค่าลายเซ็นของไฟล์ที่กำลังดู **หารด้วยค่าเดียวกันของ
normal ที่ความเร็วเดียวกัน** คำนวณสดจาก 1.28 วินาทีแรกของไฟล์ (ไม่ใช่ช่วง 67 ms
ที่วาดบนจอ เพราะ feature ที่อิงสเปกตรัมต้องการความละเอียดความถี่มากกว่านั้นมาก)
ข้างๆ กันคือ `experiment median` ซึ่งเป็น**มัธยฐานของหลายไฟล์**จากการทดลอง
ไม่ใช่ขอบเขตบน-ล่าง ไฟล์เดี่ยวหลุดออกนอกช่วงนั้นได้เป็นปกติ ให้ดูว่าอยู่คนละหลัก
หรือคนละทิศหรือเปล่ามากกว่าดูว่าตรงเป๊ะไหม

สถานะของลายเซ็นมีสามระดับ ตาม `experiments/2026-09-22-signature-persistence.md`
    [verified]  เขียว  ผ่านการทดสอบข้ามรอบบันทึกหรือเปลี่ยนตามความรุนแรงจริง
    [partial]   ส้ม    ทิศทางถูก แต่จางหายเมื่อเติมมวลถ่วง หรือไม่แยกขาดจาก normal
    [none]      แดง    ยังไม่พบลายเซ็น (overhang cage) — ไม่ไฮไลต์ช่องไหนเลย

⚠️ **ค่านี้มาจากไฟล์เดียว** ต่างจากตัวเลขในการทดลองที่เป็นมัธยฐานของหลายไฟล์
ใช้ดูแนวโน้มตอนเลื่อนได้ แต่อย่าเอาไปอ้างอิงเป็นตัวเลขผลลัพธ์
และลายเซ็นทั้งหมดคัดกรองที่ความเร็ว 20–42 Hz เท่านั้น ถ้าเลื่อนออกนอกช่วงนี้
โปรแกรมจะขึ้นข้อความเตือนต่อท้าย

**เรื่องแกน y — จุดที่สำคัญที่สุดของโปรแกรมนี้**

ถ้าปล่อยให้ matplotlib ปรับแกน y เองทุกครั้งที่เลื่อน กราฟจะดู "เท่าเดิม" ตลอด
ทั้งที่ค่าจริงโตขึ้นสิบเท่า เพราะแกนโตตามไปด้วย **ซึ่งทำลายจุดประสงค์ของโปรแกรมนี้ทั้งหมด**
โปรแกรมจึงใช้แกน y แบบ **ขยายอย่างเดียว ไม่หดกลับ** คือจำค่าสูงสุดที่เคยเห็นในแต่ละช่อง
ไว้ตลอด session พอเลื่อนไปค่าที่แรงกว่าแกนจะกว้างขึ้นแล้วค้างไว้ เลื่อนกลับมาค่าที่เบากว่า
จะเห็นเส้นแบนลงจริงๆ ถ้าอยากเริ่มนับใหม่กดปุ่ม `Rescale y`

การเปลี่ยนหมวดถือเป็นการเริ่มกวาดชุดใหม่ แกน y จึงถูกล้างให้เองอัตโนมัติ
ไม่งั้นหมวดที่สั่นเบากว่าจะถูกบีบจนเป็นเส้นตรงด้วยสเกลที่ค้างมาจากหมวดก่อนหน้า
**ผลข้างเคียงที่ต้องรู้: เทียบความสูงข้ามหมวดด้วยสายตาไม่ได้** ให้ดูตัวเลข
peak-to-peak เทียบ normal ที่มุมขวาบนของแต่ละแผงแทน ตัวนั้นเทียบข้ามหมวดได้

**ข้อควรระวัง** ตาราง (ความเร็ว × ความรุนแรง) ไม่เต็มทุกช่อง กลุ่มที่มวลถ่วงมาก
ถูกตัดปลายความเร็วสูงทิ้ง หนักสุดคือ `overhang/ball_fault` ที่ 20 g หยุดที่ 36.05 Hz
และ 35 g หยุดที่ 32.15 Hz โปรแกรมจะเลือกไฟล์ที่ความเร็ว**ใกล้ที่สุดที่มีจริง**
แล้วขึ้นข้อความเตือนสีแดงบนหัวเรื่องเมื่อค่าที่ได้ห่างจากที่ขอเกิน 1.5 Hz

⚠️ แต่ละจุดคือ**ไฟล์เดียว และช่วงเวลาสั้นๆ ช่วงเดียว** ใช้หาแนวโน้มและจุดที่น่าสงสัย
ตัวเลขที่ยืนยันแล้วด้วยหลายไฟล์อยู่ใน `reports/eda/README-raw-channels.md`

ปุ่มเลือกหมวดทางซ้าย **คลิกที่ไหนก็ได้ในแถว** ไม่ต้องเล็งวงกลม

แป้นลัด: ← → เปลี่ยนความเร็วทีละ 1 Hz · ↑ ↓ เปลี่ยนความรุนแรงทีละระดับ

รัน:
    python src/viz/browse_waveforms.py
    python src/viz/browse_waveforms.py --window-ms 40 --target-hz 45
"""

from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Button, RadioButtons, Slider

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.features.screen_signatures import channel_features  # noqa: E402
from src.paths import sampling_rate  # noqa: E402
from src.viz import style  # noqa: E402
from src.viz.explore_raw_channels import CHANNELS  # noqa: E402
from src.viz.widgets import row_clickable  # noqa: E402

FS = sampling_rate()

HZ_MIN, HZ_MAX = 12.0, 62.0
SPEED_WARN_HZ = 1.5      # ห่างจากที่ขอเกินนี้ถือว่าไม่มีข้อมูลตรงจุดนั้น
CACHE_SIZE = 16          # ไฟล์ที่อ่านแล้วเก็บไว้กี่ไฟล์

# จำนวนแถวที่เก็บไว้คำนวณค่าลายเซ็น = 1.28 วินาที ให้ความละเอียดความถี่ 0.78 Hz
# ยาวกว่าหน้าต่างที่วาดบนจอมาก เพราะ feature อย่าง h1_frac กับ r21 ต้องแยกพีค
# 1x กับ 2x ให้ออก ซึ่งหน้าต่าง 67 ms (0.067 s -> 15 Hz ต่อช่อง) ทำไม่ได้เลย
FEAT_N = 65536
FEAT_TOL_HZ = 2.5 * FS / FEAT_N

# ช่วงความเร็วที่การคัดกรองลายเซ็นใช้ทดสอบ นอกช่วงนี้ตัวเลขยังคำนวณได้
# แต่ไม่เคยถูกตรวจสอบ จึงต้องบอกผู้ใช้ให้รู้
VALIDATED_HZ = (20.0, 42.0)


class Signature:
    """ลายเซ็นของหมวดหนึ่ง — ช่องเซ็นเซอร์และ feature ที่ใช้เป็นตัววัด

    ที่มาของทุกบรรทัด: `experiments/2026-09-22-signature-screen.md`
    (คัดกรอง 66 feature ด้วย AUC one-vs-rest) แล้วกรองอีกชั้นด้วย
    `...-signature-persistence.md` ที่ทดสอบว่าลายเซ็นคงอยู่ข้ามรอบบันทึก
    หรือเปลี่ยนตามความรุนแรงจริงไหม ตัวที่ไม่ผ่านถูกตัดทิ้งไปแล้ว
    """

    def __init__(self, channel: str, feature: str, up: bool, status: str,
                 expected: str, note: str):
        self.channel = channel
        self.feature = feature
        self.up = up              # True = สูงกว่า normal, False = ต่ำกว่า
        self.status = status      # "ok" / "partial" / "none"
        self.expected = expected  # ช่วงที่วัดไว้ เทียบเป็นเท่าของ normal
        self.note = note


STATUS_MARK = {"ok": "[verified]", "partial": "[partial]", "none": "[none]"}
STATUS_COLOR = {"ok": "#1b7a3d", "partial": "#b07500", "none": "#c2352b"}

SIGNATURES = {
    "Imbalance": Signature(
        "u_radial", "h1_frac", True, "ok", "2.9-13.6x, rises with mass",
        "energy share at 1x - the textbook imbalance signature"),
    "H-misalign": Signature(
        "o_tang", "r21", True, "partial", "1.6-4.8x",
        "2x/1x peak ratio - direction right, never fully separated"),
    "V-misalign": Signature(
        "o_tang", "r21", True, "partial", "1.9-6.1x",
        "2x/1x peak ratio - direction right, never fully separated"),
    "Under ball": Signature(
        "o_axial", "rms", True, "ok", "5-12x at every mass",
        "overall level on the far-end axial channel"),
    "Under cage": Signature(
        "u_tang", "kurt", True, "partial", "1.7-1.9x at 0 and 6 g only",
        "raw kurtosis - washed out by the 1x sine once mass is added"),
    "Under outer": Signature(
        "o_axial", "e_high", True, "partial", "9.5x at 0 g, fades with mass",
        "2-10 kHz energy share - diluted once imbalance fills the low band"),
    "Over ball": Signature(
        "o_radial", "e_high", False, "ok", "near 0 at every mass",
        "channel swamped by a ~9.93x shaft component, high band collapses"),
    "Over cage": Signature(
        "o_tang", "env_floor", True, "none", "no signature found yet",
        "screening picked env_floor but it runs 5x QUIETER than normal"),
    "Over outer": Signature(
        "u_radial", "env_rel", True, "ok", "1.35x at every mass",
        "envelope floor / 2-5 kHz level, so sensor gain cancels out"),
}


class Category:
    """หนึ่งหมวดที่เลือกได้ พร้อมวิธีไล่ระดับความรุนแรงของหมวดนั้น

    ``level_col`` คือคอลัมน์ในดัชนีที่ใช้แยกระดับ ซึ่งไม่เหมือนกันทุกหมวด
    imbalance กับ bearing ใช้มวลถ่วงเป็นตัวเลข ส่วน misalignment ใช้ชื่อ subclass
    ที่เป็นสตริง เช่น ``1.0mm`` จึงต้องเรียงลำดับด้วยค่าตัวเลขที่แกะจากสตริง
    """

    def __init__(self, label: str, cls: str, subclass: str | None,
                 level_col: str, unit: str):
        self.label = label
        self.cls = cls
        self.subclass = subclass
        self.level_col = level_col
        self.unit = unit

    def levels(self, index: pd.DataFrame) -> list:
        sel = index[index["cls"] == self.cls]
        if self.subclass is not None:
            sel = sel[sel["subclass"] == self.subclass]
        vals = sel[self.level_col].unique().tolist()
        if self.level_col == "mass_g":
            return sorted(vals)
        return sorted(vals, key=lambda v: float(str(v).rstrip("m")))

    def level_text(self, value) -> str:
        return f"{value} {self.unit}" if self.unit == "g" else str(value)

    def kwargs(self, value) -> dict:
        if self.level_col == "mass_g":
            return {"subclass": self.subclass, "mass_g": int(value)}
        return {"subclass": str(value)}


CATEGORIES = [
    Category("Imbalance", "imbalance", None, "mass_g", "g"),
    Category("H-misalign", "horizontal-misalignment", None, "subclass", "mm"),
    Category("V-misalign", "vertical-misalignment", None, "subclass", "mm"),
    Category("Under ball", "underhang", "ball_fault", "mass_g", "g"),
    Category("Under cage", "underhang", "cage_fault", "mass_g", "g"),
    Category("Under outer", "underhang", "outer_race", "mass_g", "g"),
    Category("Over ball", "overhang", "ball_fault", "mass_g", "g"),
    Category("Over cage", "overhang", "cage_fault", "mass_g", "g"),
    Category("Over outer", "overhang", "outer_race", "mass_g", "g"),
]


class Browser:
    def __init__(self, index: pd.DataFrame, target_hz: float, window_ms: float):
        self.index = index
        self.n = int(window_ms / 1000.0 * FS)
        self.t = np.arange(self.n) / FS * 1000.0
        self.window_ms = window_ms
        self.cat = CATEGORIES[0]
        self.levels = self.cat.levels(index)
        self.level_i = len(self.levels) - 1        # เริ่มที่ความรุนแรงมากสุด
        self.want_hz = target_hz
        self.cache: OrderedDict[str, pd.DataFrame] = OrderedDict()
        self.ymax = {ch: 0.0 for ch in CHANNELS}   # แกน y ที่เคยกว้างสุด
        self.shown: tuple | None = None            # (path, normal path) ที่วาดอยู่
        self._sig_value = float("nan")             # ค่าลายเซ็นของไฟล์ที่วาดอยู่

        self._build()
        self._redraw()

    # ---------- การอ่านไฟล์ ----------

    def _load(self, path) -> pd.DataFrame:
        key = str(path)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        # เก็บยาวกว่าที่วาดบนจอ เพราะต้องใช้คำนวณค่าลายเซ็นด้วย
        d = mf.load(path, CHANNELS).iloc[:max(FEAT_N, self.n)]
        self.cache[key] = d
        if len(self.cache) > CACHE_SIZE:
            self.cache.popitem(last=False)
        return d

    def _pick(self):
        """คืน (แถวของไฟล์ที่เลือก, แถวของ normal ที่ความเร็วเดียวกัน)"""
        level = self.levels[self.level_i]
        row = mf.pick_matched_speed(self.index, self.want_hz, self.cat.cls,
                                    **self.cat.kwargs(level))
        got_hz = float(mf.speed_hz(row.to_frame().T).iloc[0])
        ref = mf.pick_matched_speed(self.index, got_hz, "normal")
        return row, ref, got_hz, level

    # ---------- หน้าตา ----------

    def _build(self) -> None:
        self.fig = plt.figure(figsize=(12.0, 9.6))
        self.fig.canvas.manager.set_window_title("MAFAULDA raw waveform browser")

        self.axes, self.names = [], []
        top, bottom, gap = 0.882, 0.155, 0.006
        h = (top - bottom) / len(CHANNELS) - gap
        for i, ch in enumerate(CHANNELS):
            ax = self.fig.add_axes((0.20, top - (h + gap) * (i + 1), 0.775, h))
            # ชื่อช่องวางในแผง ไม่ใช่เป็น ylabel เพราะ tick label ของแต่ละแถว
            # ยาวไม่เท่ากัน (แกนบางแถวเป็นหลักสิบ บางแถวเป็น 0.05) ylabel จึงขยับ
            # เข้าออกจนชนตัวเลขและอ่านไม่ออก
            self.names.append(
                ax.annotate(f"{ch}  (g)", xy=(0.006, 0.93), xycoords="axes fraction",
                            ha="left", va="top", fontsize=9, color=style.INK_SOFT))
            if i < len(CHANNELS) - 1:
                ax.set_xticklabels([])
            else:
                ax.set_xlabel("Time (ms)", fontsize=8.5)
            ax.set_xlim(0, self.window_ms)
            self.axes.append(ax)

        # เส้น normal วาดก่อนเพื่อให้อยู่ข้างหลัง
        self.ref_lines = [ax.plot([], [], color=style.REFERENCE, lw=0.5, zorder=1)[0]
                          for ax in self.axes]
        self.lines = [ax.plot([], [], lw=0.6, zorder=2)[0] for ax in self.axes]
        self.notes = [ax.annotate("", xy=(0.995, 0.93), xycoords="axes fraction",
                                  ha="right", va="top", fontsize=8, color=style.INK)
                      for ax in self.axes]

        ax_radio = self.fig.add_axes((0.012, 0.42, 0.155, 0.47))
        ax_radio.set_title("Fault group", fontsize=9, loc="left", pad=6)
        ax_radio.set_facecolor(style.SURFACE)
        for s in ax_radio.spines.values():
            s.set_visible(False)
        ax_radio.grid(False)
        self.radio = RadioButtons(ax_radio, [c.label for c in CATEGORIES], active=0,
                                  radio_props={"s": 110.0})
        for lbl in self.radio.labels:
            lbl.set_fontsize(9)
        self.radio.on_clicked(self._on_category)
        # วงกลมค่าเริ่มต้นโตแค่ 7 พิกเซล กดยากมาก จึงรับคลิกทั้งแถว
        row_clickable(self.radio)

        ax_speed = self.fig.add_axes((0.20, 0.075, 0.70, 0.022))
        self.s_speed = Slider(ax_speed, "Shaft speed  ", HZ_MIN, HZ_MAX,
                              valinit=self.want_hz, valfmt="%.1f Hz",
                              color=style.CLASS_COLORS["normal"])
        self.s_speed.on_changed(self._on_speed)

        self.ax_level = self.fig.add_axes((0.20, 0.030, 0.70, 0.022))
        self.s_level: Slider | None = None
        self._build_level_slider()

        # ปุ่มอยู่คอลัมน์ซ้าย ไม่ใช่ท้ายแถบเลื่อน เพราะตรงนั้นเป็นที่ของตัวเลขค่าปัจจุบัน
        ax_btn = self.fig.add_axes((0.020, 0.028, 0.085, 0.030))
        self.btn = Button(ax_btn, "Rescale y", color=style.SURFACE,
                          hovercolor=style.GRID)
        self.btn.label.set_fontsize(8.5)
        self.btn.on_clicked(self._on_rescale)

        self.fig.text(0.012, 0.115,
                      "Arrow keys:\n  left/right  speed\n  up/down  severity",
                      fontsize=8, color=style.INK_SOFT, va="top")
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _build_level_slider(self) -> None:
        """สร้างแถบความรุนแรงใหม่ทุกครั้งที่เปลี่ยนหมวด เพราะจำนวนระดับไม่เท่ากัน

        imbalance มี 7 ระดับ, vertical misalignment 6, horizontal 4, bearing 4
        matplotlib เปลี่ยนช่วงของ Slider ที่สร้างแล้วไม่ได้ จึงต้องสร้างทับลงไปใหม่
        """
        self.ax_level.clear()
        label = "Mass  " if self.cat.unit == "g" else "Offset  "
        self.s_level = Slider(self.ax_level, label, 0, len(self.levels) - 1,
                              valinit=self.level_i, valstep=1,
                              color=style.CLASS_COLORS["imbalance"])
        self.s_level.valtext.set_text(self.cat.level_text(self.levels[self.level_i]))
        self.s_level.on_changed(self._on_level)

    # ---------- การตอบสนอง ----------

    def _on_category(self, label: str) -> None:
        self.cat = next(c for c in CATEGORIES if c.label == label)
        self.levels = self.cat.levels(self.index)
        self.level_i = min(self.level_i, len(self.levels) - 1)
        self._build_level_slider()
        # เปลี่ยนหมวด = เริ่มกวาดชุดใหม่ ถ้าไม่ล้างแกนที่ค้างไว้ หมวดที่สั่นเบา
        # จะถูกบีบจนเป็นเส้นตรงด้วยสเกลของหมวดก่อนหน้า
        self.ymax = {ch: 0.0 for ch in CHANNELS}
        self._redraw(force=True)

    def _on_speed(self, val: float) -> None:
        self.want_hz = float(val)
        self._redraw()

    def _on_level(self, val: float) -> None:
        self.level_i = int(val)
        self.s_level.valtext.set_text(self.cat.level_text(self.levels[self.level_i]))
        self._redraw()

    def _on_rescale(self, _event) -> None:
        self.ymax = {ch: 0.0 for ch in CHANNELS}
        self._redraw(force=True)

    def _on_key(self, event) -> None:
        if event.key in ("left", "right"):
            step = 1.0 if event.key == "right" else -1.0
            self.s_speed.set_val(float(np.clip(self.want_hz + step, HZ_MIN, HZ_MAX)))
        elif event.key in ("up", "down"):
            step = 1 if event.key == "up" else -1
            self.s_level.set_val(int(np.clip(self.level_i + step, 0, len(self.levels) - 1)))

    # ---------- การวาด ----------

    def _redraw(self, force: bool = False) -> None:
        row, ref, got_hz, level = self._pick()

        # เลื่อนแถบความเร็วไปมาในช่วงที่ยังได้ไฟล์เดิม ไม่ต้องอ่านไฟล์ใหม่
        key = (str(row["path"]), str(ref["path"]))
        if key == self.shown and not force:
            # ไฟล์เดิม หมวดเดิม ค่าลายเซ็นจึงเท่าเดิม ใช้ค่าที่คำนวณไว้แล้ว
            self._title(row, got_hz, level, SIGNATURES[self.cat.label], self._sig_value)
            self.fig.canvas.draw_idle()
            return
        self.shown = key

        data = self._load(row["path"])
        ref_data = self._load(ref["path"])
        color = style.color(self.cat.cls)
        sig = SIGNATURES[self.cat.label]

        for i, (ax, line, rline, note, ch) in enumerate(
                zip(self.axes, self.lines, self.ref_lines, self.notes, CHANNELS)):
            v = data[ch].to_numpy()
            v = v - v.mean()
            r = ref_data[ch].to_numpy()
            r = r - r.mean()
            vd, rd = v[:self.n], r[:self.n]

            line.set_data(self.t, vd)
            line.set_color(color)
            rline.set_data(self.t, rd)

            # แกน y ขยายอย่างเดียว ไม่หดกลับ เพื่อให้เห็นว่าค่าโตขึ้นหรือเล็กลงจริง
            self.ymax[ch] = max(self.ymax[ch],
                                float(np.abs(vd).max()), float(np.abs(rd).max()))
            lim = self.ymax[ch] * 1.05 or 1.0
            ax.set_ylim(-lim, lim)

            ref_p2p = float(rd.max() - rd.min())
            ratio = float(vd.max() - vd.min()) / ref_p2p if ref_p2p > 0 else np.nan
            note.set_text(f"{ratio:.2f}x")

            self._mark_signature(i, ax, ch, sig)

        self._sig_value = self._signature_value(data, ref_data, sig, got_hz)
        self._title(row, got_hz, level, sig, self._sig_value)
        self.fig.canvas.draw_idle()

    # ---------- ลายเซ็น ----------

    def _mark_signature(self, i: int, ax, ch: str, sig: Signature) -> None:
        """ไฮไลต์แผงของช่องที่เป็นตัววัดของหมวดนี้

        หมวดที่ยังไม่มีลายเซ็น (over cage) ไม่ไฮไลต์อะไรเลย เพราะการไฮไลต์
        ช่องที่เรายังพิสูจน์ไม่ได้ จะทำให้คนอ่านเข้าใจว่ามีตัววัดแล้ว
        """
        on = ch == sig.channel and sig.status != "none"
        ax.set_facecolor("#f2f4ef" if on else style.SURFACE)
        self.names[i].set_text(
            f"{ch}  (g)   <- signature: {sig.feature}" if on else f"{ch}  (g)")
        self.names[i].set_color(STATUS_COLOR[sig.status] if on else style.INK_SOFT)
        self.names[i].set_fontweight("bold" if on else "normal")

    def _signature_value(self, data: pd.DataFrame, ref_data: pd.DataFrame,
                         sig: Signature, rot: float) -> float:
        """ค่าลายเซ็นของไฟล์ที่กำลังดู หารด้วยค่าเดียวกันของ normal ที่ความเร็วเดียวกัน

        คำนวณบน 1.28 วินาทีแรกของไฟล์ ไม่ใช่ช่วง 67 ms ที่วาดบนจอ เพราะ feature
        ที่อิงสเปกตรัมต้องการความละเอียดความถี่มากกว่านั้นมาก
        """
        if sig.status == "none":
            return float("nan")
        n = min(FEAT_N, len(data), len(ref_data))
        a = channel_features(data[sig.channel].to_numpy()[:n], rot,
                             tol_hz=FEAT_TOL_HZ)[sig.feature]
        b = channel_features(ref_data[sig.channel].to_numpy()[:n], rot,
                             tol_hz=FEAT_TOL_HZ)[sig.feature]
        return a / b if b else float("nan")

    def _title(self, row, got_hz: float, level, sig: Signature, value: float) -> None:
        miss = abs(got_hz - self.want_hz)
        head = (f"{self.cat.label}  ·  {self.cat.level_text(level)}  ·  "
                f"{got_hz:.2f} Hz ({got_hz * 60:.0f} rpm)")
        if miss > SPEED_WARN_HZ:
            head += f"   ⚠ no data near {self.want_hz:.1f} Hz here"
        sub = (f"{row['rel']}   |   grey = Normal at the same speed   |   "
               f"number = peak-to-peak vs Normal over the {self.window_ms:.0f} ms shown"
               f"   |   y axis grows, never shrinks")

        if sig.status == "none":
            sig_txt = (f"{STATUS_MARK[sig.status]} no verified signature for this fault "
                       f"- {sig.note}")
        else:
            arrow = "higher" if sig.up else "lower"
            sig_txt = (f"{STATUS_MARK[sig.status]} {sig.channel}.{sig.feature} "
                       f"{arrow} than Normal   |   this file: {value:.2f}x   |   "
                       f"experiment median {sig.expected}   |   {sig.note}")
            if not VALIDATED_HZ[0] <= got_hz <= VALIDATED_HZ[1]:
                sig_txt += (f"   |   only validated at "
                            f"{VALIDATED_HZ[0]:.0f}-{VALIDATED_HZ[1]:.0f} Hz")

        if not hasattr(self, "_t1"):
            self._t1 = self.fig.text(0.20, 0.982, "", fontsize=12.5,
                                     fontweight="bold", color=style.INK, va="top")
            self._t2 = self.fig.text(0.20, 0.947, "", fontsize=8,
                                     color=style.INK_SOFT, va="top")
            self._t3 = self.fig.text(0.20, 0.922, "", fontsize=8, va="top")
        self._t1.set_text(head)
        self._t1.set_color("#c2352b" if miss > SPEED_WARN_HZ else style.INK)
        self._t2.set_text(sub)
        self._t3.set_text(sig_txt)
        self._t3.set_color(STATUS_COLOR[sig.status])


def main() -> int:
    ap = argparse.ArgumentParser(description="เลื่อนดูสัญญาณดิบตามความเร็วและความรุนแรง")
    ap.add_argument("--target-hz", type=float, default=30.0, help="ความเร็วเริ่มต้น (Hz)")
    ap.add_argument("--window-ms", type=float, default=67.0,
                    help="ความกว้างหน้าต่างเวลา (ms) ค่าเริ่มต้นราว 2 รอบที่ 30 Hz")
    args = ap.parse_args()

    if plt.get_backend().lower() == "agg":
        print("matplotlib กำลังใช้ backend 'agg' ซึ่งเปิดหน้าต่างไม่ได้\n"
              "บน Windows ปกติจะได้ TkAgg มาให้อยู่แล้ว ถ้าไม่ได้ให้ติดตั้ง tkinter\n"
              "บน Raspberry Pi แบบไม่มีจอ โปรแกรมนี้ใช้ไม่ได้ ต้องรันบนโน้ตบุ๊ก",
              file=sys.stderr)
        return 1

    style.apply()
    Browser(mf.build_index(), args.target_hz, args.window_ms)
    plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

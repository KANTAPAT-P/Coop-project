"""Bubble plot ของทั้ง dataset — เห็นแนวโน้มทั้งสองแกนพร้อมกันในภาพเดียว

`browse_waveforms.py` ให้ดูทีละจุด ต้องเลื่อนแถบไปเรื่อยๆ แล้วจำเอาเองว่าค่าที่มุมขวาบน
เปลี่ยนไปยังไง โปรแกรมนี้เอาค่าของ**ทุกไฟล์**มาวางในภาพเดียว

    แกน X    มวลถ่วง (g) หรือระยะเยื้องศูนย์ (mm) แล้วแต่คลาส
    แกน Y    ความเร็วรอบ (Hz)
    ขนาดวง   ค่าของ feature ที่เลือก เทียบกับ normal ที่ความเร็วเดียวกัน
    สีวง     ค่าเดียวกันในสเกล log — แดง = สูงกว่า normal, น้ำเงิน = ต่ำกว่า

**เลือก feature ได้ 12 ตัว** ไม่ใช่แค่ความแรงอย่างเดียว ซึ่งจำเป็นเพราะลายเซ็น
ส่วนใหญ่**ไม่ใช่เรื่องความแรง** เช่น misalignment ใช้ `r21` (อัตราส่วนพีค 2×/1×)
เพราะมันย้ายพลังงานจาก 1× ไป 2× โดยที่ความแรงรวมเท่าเดิม กราฟที่พล็อต `p2p`
จึงมองลายเซ็นตัวนั้นไม่เห็นตามนิยาม ปุ่ม `signature` กระโดดไปที่ช่องและ feature
ที่เป็นลายเซ็นของคลาสนั้นให้ทันที

**แถบ `Normal` ทางซ้ายคือพื้นความคลาดเคลื่อน** เป็น normal ทั้ง 49 ไฟล์เทียบกับ
เส้นฐานของตัวเอง มัธยฐานจึงเป็น 1.00 เสมอตามนิยาม สิ่งที่มันบอกคือ**ความกระจาย**
รอบ 1.0 ซึ่งคือความแปรปรวนที่เครื่อง**ปกติ**สร้างขึ้นเองจากรอบบันทึกและการวัด
**ความเสียหายจะน่าเชื่อถือก็ต่อเมื่อดันค่าออกไปไกลกว่าแถบนี้**

แถบนี้แยกแกนออกมาต่างหาก **ไม่เอาไปต่อท้ายแกน X เดียวกัน** เพราะ x = 0 ของคลาส
bearing หมายถึง "มวลถ่วง 0 กรัม" ซึ่งเป็นตลับลูกปืนที่เสียแล้ว ไม่ใช่เครื่องปกติ

**ทำไมต้องใส่สีด้วยทั้งที่ขนาดบอกอยู่แล้ว** เพราะขนาดวงกลมบอกค่าที่**น้อยกว่า 1**
ไม่ได้ วงเล็กจิ๋วแยกไม่ออกระหว่าง "ต่ำกว่า normal 5 เท่า" กับ "เท่ากับ normal"
ทั้งที่ต่างกันสิ้นเชิง (h-misalign ทำให้ `o_axial` เบาลง 3 เท่า ซึ่งเป็นลายเซ็น
ที่ชัดที่สุดอันหนึ่ง) สีบอกทิศทาง ขนาดบอกขนาด และช่วยตอนวงซ้อนกันด้วย

**สเกลสีคงที่ต่อหนึ่ง feature** คำนวณจากการกระจายของ feature นั้นทั้ง dataset
จึงเทียบข้ามคลาสและข้ามช่องได้ตรงๆ แต่เทียบข้าม feature ไม่ได้ (คนละหน่วย)
ส่วน**ขนาดวงปรับตามค่ามากสุดของภาพที่กำลังดู** จึงเทียบขนาดข้ามภาพไม่ได้
ค่ามากสุดพิมพ์ไว้บนหัวเรื่องแล้ว

## ข้อควรระวังที่โปรแกรมกันไว้ให้แล้ว

1. **ไม่มีช่อง `mic`** เพราะสเกลของคลาส imbalance ต่างจากคลาสอื่น 88 เท่า
2. **แถบเทาบนแกน y คือนอกช่วง 20–42 Hz** ซึ่งเป็นช่วงเดียวที่ลายเซ็นถูกคัดกรอง
   และทดสอบ นอกแถบนั้นตัวเลขยังคำนวณได้แต่ไม่เคยถูกตรวจสอบ
   ยิ่งต่ำกว่า 15 Hz ยิ่งต้องระวัง เพราะ high-pass 10 Hz เริ่มกินพีค 1×
3. **`o_radial` มีระดับสัญญาณต่ำกว่าช่องอื่นราว 20 เท่า และเส้นฐานไม่นิ่ง**
   (normal ไฟล์หนึ่งสูงถึง 2.69 เท่าของเส้นฐานตัวเอง) โปรแกรมเตือนให้เมื่อเลือก
4. **กราฟนี้ไม่ได้พิสูจน์ว่าอะไรเป็นลายเซ็น** แต่ละจุดคือไฟล์เดียว และทั้งคอลัมน์
   มาจากรอบบันทึกเดียวกัน อะไรที่ต่างกันทั้งคอลัมน์เท่าๆ กันโดยไม่เปลี่ยนตาม
   ความรุนแรง คือร่องรอยของรอบบันทึก ไม่ใช่ของความเสียหาย

ปุ่มทางซ้าย **คลิกที่ไหนก็ได้ในแถว** ไม่ต้องเล็งวงกลม · คลิกที่วงไหนในกราฟบอกชื่อไฟล์

ต้องมีตาราง `data/processed/feature_grid.csv` ก่อน สร้างด้วย
    python src/features/feature_grid.py        (ราว 16 นาที)

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
from matplotlib.widgets import Button, RadioButtons

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.features.feature_grid import FEATURES  # noqa: E402
from src.paths import processed_dir  # noqa: E402
from src.viz import style  # noqa: E402
from src.viz.browse_waveforms import CATEGORIES, SIGNATURES, STATUS_COLOR  # noqa: E402
from src.viz.explore_raw_channels import CHANNELS  # noqa: E402
from src.viz.widgets import row_clickable  # noqa: E402

AREA_MIN, AREA_MAX = 14.0, 460.0        # ขนาดวงเป็น point^2
# ขนาดวงกลมของปุ่มเรดิโอ (point^2) วัดแล้วที่ 110 ข้อความทับวงกลม เพราะ
# matplotlib คำนวณระยะเยื้องข้อความจากขนาดเริ่มต้น ไม่ได้ปรับตาม radio_props
# ที่ 40 ได้วงโต 8.8 px เหลือช่องว่าง 3.2 px และไม่ต้องโตกว่านี้แล้ว
# เพราะ row_clickable ทำให้กดได้ทั้งช่องอยู่แล้ว วงกลมมีไว้ให้เห็นว่าเลือกอะไร
RADIO_SIZE = 40.0
SIZE_LEGEND_FRAC = (0.15, 0.5, 1.0)     # สัดส่วนของค่ามากสุด ที่เอามาทำตัวอย่างขนาด
VALIDATED_HZ = (20.0, 42.0)             # ช่วงที่คัดกรองและทดสอบลายเซ็นไว้
SPEED_LIM = (10.0, 64.0)

# normal ที่ใช้เป็นฐานเทียบมีไฟล์เดียวต่อความเร็ว ค่าจึงกระเพื่อม
# ใช้มัธยฐานเคลื่อนที่ 3 จุด (กว้างราว 3 Hz) ให้เส้นฐานนิ่งก่อนเอาไปหาร
REF_SMOOTH = 3

# เปอร์เซ็นไทล์ที่ใช้กำหนดปลายสเกลสีของแต่ละ feature และขอบเขตที่ยอมให้
COLOR_PCT = 98.0
COLOR_DECADES = (0.3, 2.0)

# ชื่อที่อ่านออก และความหมายหนึ่งบรรทัดของแต่ละ feature
FEATURE_INFO = {
    "p2p":       ("peak-to-peak", "height of the raw waveform - what browse_waveforms shows"),
    "rms":       ("RMS level", "overall vibration energy"),
    "kurt":      ("kurtosis (raw)", "spikiness of the raw signal; pure sine 1.5, Gaussian 3"),
    "crest":     ("crest factor", "peak divided by RMS"),
    "h1_frac":   ("1x energy share", "energy at shaft speed - the imbalance signature"),
    "r21":       ("2x / 1x ratio", "energy moved from 1x to 2x - the misalignment signature"),
    "e_low":     ("energy 5Hz-10x", "share of energy below the 10th harmonic"),
    "e_mid":     ("energy 10x-2kHz", "share of energy in the mid band"),
    "e_high":    ("energy 2-10kHz", "share of energy where bearing impacts ring"),
    "kurt_band": ("kurtosis 2-5kHz", "impact sharpness after bandpass"),
    "env_floor": ("envelope floor", "median of the envelope spectrum - random impacting"),
    "env_rel":   ("envelope floor / band", "env_floor over the 2-5kHz level; gain cancels"),
}

# คำเตือนเฉพาะช่อง เขียนไว้ตอนตรวจ dataset (CLAUDE.md หัวข้อ 5)
CHANNEL_NOTE = {
    "o_radial": "CAUTION  o_radial sits ~20x lower than the other channels and its "
                "Normal baseline is unstable (one healthy file reaches 2.69x)",
}


def level_values(tab: pd.DataFrame, cat) -> pd.Series:
    """ค่าที่จะไปอยู่บนแกน X ของคลาสนี้ — มวลถ่วง (g) หรือระยะเยื้องศูนย์ (mm)"""
    return tab["severity"] if cat.unit == "mm" else tab["mass_g"]


def load_table() -> tuple[pd.DataFrame, list[str]]:
    """อ่านตาราง feature คืน (ตาราง, รายชื่อ feature ที่ใช้ได้จริง)

    ถ้ายังไม่มี `feature_grid.csv` แต่มี `p2p_grid.csv` เดิมอยู่ ก็ยังเปิดได้
    โดยเลือกได้แค่ p2p ตัวเดียว จะได้ไม่ต้องรอ 16 นาทีก่อนใช้งานครั้งแรก
    """
    full = processed_dir() / "feature_grid.csv"
    old = processed_dir() / "p2p_grid.csv"
    if full.is_file():
        tab = pd.read_csv(full, keep_default_na=False, na_values=[""])
    elif old.is_file():
        tab = pd.read_csv(old, keep_default_na=False, na_values=[""])
        tab = tab.rename(columns={f"p2p_{c}": f"{c}.p2p" for c in CHANNELS})
        print("ยังไม่มี feature_grid.csv จึงเปิดได้เฉพาะ p2p\n"
              "สร้างตารางเต็มด้วย  python src/features/feature_grid.py")
    else:
        raise FileNotFoundError(
            "ไม่พบทั้ง feature_grid.csv และ p2p_grid.csv\n"
            "สร้างก่อนด้วย  python src/features/feature_grid.py")

    tab["severity"] = pd.to_numeric(tab["severity"], errors="coerce")
    feats = [f for f in FEATURES if all(f"{c}.{f}" in tab.columns for c in CHANNELS)]
    return tab, feats


class BubbleGrid:
    def __init__(self, tab: pd.DataFrame, features: list[str]):
        self.tab = tab
        self.features = features
        self.cat = CATEGORIES[0]
        sig = SIGNATURES[self.cat.label]
        self.channel = sig.channel
        self.feature = sig.feature if sig.feature in features else features[0]
        self.points = pd.DataFrame()
        self.ref_points = pd.DataFrame()
        self._mute = False          # กันไม่ให้ callback ของปุ่มวาดซ้ำ
        self._ref_cache: dict[str, tuple] = {}
        self._norm_cache: dict[str, float] = {}
        self._build()
        self._redraw()

    # ---------- ข้อมูล ----------

    def _baseline(self, col: str) -> tuple[np.ndarray, np.ndarray]:
        """เส้นฐาน normal ของคอลัมน์หนึ่ง เป็นฟังก์ชันของความเร็วรอบ"""
        if col not in self._ref_cache:
            n = self.tab[self.tab["cls"] == "normal"].sort_values("rot_hz_used")
            y = n[col].rolling(REF_SMOOTH, center=True, min_periods=1).median()
            self._ref_cache[col] = (n["rot_hz_used"].to_numpy(), y.to_numpy())
        return self._ref_cache[col]

    def _ratio(self, sel: pd.DataFrame, col: str) -> np.ndarray:
        x, y = self._baseline(col)
        base = np.interp(sel["rot_hz_used"].to_numpy(), x, y)
        with np.errstate(divide="ignore", invalid="ignore"):
            r = sel[col].to_numpy() / base
        # เส้นฐานเป็นศูนย์หรือติดลบ = หารไม่ได้ ทิ้งจุดนั้นไปดีกว่าวาดค่ามั่ว
        return np.where(np.isfinite(r) & (base > 0), r, np.nan)

    def _frame(self, sel: pd.DataFrame, xs) -> pd.DataFrame:
        col = f"{self.channel}.{self.feature}"
        return pd.DataFrame({
            "x": xs,
            "y": sel["rot_hz_used"].to_numpy(),
            "ratio": self._ratio(sel, col),
            "rel": sel["rel"].to_numpy(),
        }).dropna()

    def _select(self) -> pd.DataFrame:
        sel = self.tab[self.tab["cls"] == self.cat.cls]
        if self.cat.subclass is not None:
            sel = sel[sel["subclass"] == self.cat.subclass]
        return self._frame(sel, level_values(sel, self.cat).to_numpy())

    def _select_normal(self) -> pd.DataFrame:
        """normal 49 ไฟล์ เทียบกับเส้นฐานของตัวเอง = พื้นความคลาดเคลื่อน"""
        sel = self.tab[self.tab["cls"] == "normal"]
        return self._frame(sel, np.full(len(sel), 0.5))

    def _color_span(self) -> float:
        """ปลายสเกลสีของ feature ปัจจุบัน หน่วยเป็นจำนวน decade ของ log10

        คิดจากการกระจายของ feature นั้น**ทั้ง dataset ทุกช่อง** ไม่ใช่เฉพาะภาพที่ดูอยู่
        สเกลจึงคงที่เมื่อสลับคลาสหรือสลับช่อง ทำให้เทียบกันได้ แต่เปลี่ยนเมื่อสลับ
        feature เพราะแต่ละตัวมีช่วงต่างกันคนละโลก (kurt แกว่งไม่ถึงเท่าตัว
        ขณะที่ e_high ต่างกันเป็นร้อยเท่า) ถ้าใช้สเกลเดียวกันหมด kurt จะขาวโพลน
        """
        if self.feature not in self._norm_cache:
            vals = []
            for ch in CHANNELS:
                r = self._ratio(self.tab, f"{ch}.{self.feature}")
                r = r[np.isfinite(r) & (r > 0)]
                if len(r):
                    vals.append(np.abs(np.log10(r)))
            span = np.percentile(np.concatenate(vals), COLOR_PCT) if vals else 1.0
            self._norm_cache[self.feature] = float(np.clip(span, *COLOR_DECADES))
        return self._norm_cache[self.feature]

    # ---------- หน้าตา ----------

    def _build(self) -> None:
        self.fig = plt.figure(figsize=(13.8, 9.0))
        if self.fig.canvas.manager is not None:
            self.fig.canvas.manager.set_window_title("MAFAULDA bubble grid")

        # ⚠️ กับดักคลาสสิกของ matplotlib: CallbackRegistry เก็บ callback ที่เป็น
        # bound method ไว้เป็น **weak reference** ถ้าไม่มีใครถืออ็อบเจกต์นี้ไว้
        # Python จะเก็บกวาดมันทิ้งทันทีที่ __init__ คืนค่า แล้ว callback ทุกตัวก็ตาย
        # เงียบๆ อาการที่เห็นคือ **ปุ่มติ๊กได้แต่กราฟไม่อัปเดต** เพราะตัว widget เอง
        # ยังมีชีวิตอยู่ ผูกตัวเองไว้กับ figure ซึ่ง pyplot ถือไว้ให้ตลอดอายุหน้าต่าง
        self.fig._edge_pdm_app = self

        self.norm = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)

        # แถบ normal แยกแกนต่างหาก ดูเหตุผลใน docstring หัวไฟล์
        self.ax_ref = self.fig.add_axes((0.264, 0.095, 0.042, 0.760))
        self.ax_ref.set_ylabel("Shaft speed (Hz)")
        self.ax_ref.set_xlim(0, 1)
        self.ax_ref.set_xticks([0.5])
        self.ax_ref.set_xticklabels(["Normal"], fontsize=9)
        self.ax_ref.set_ylim(*SPEED_LIM)

        self.ax = self.fig.add_axes((0.332, 0.095, 0.518, 0.760), sharey=self.ax_ref)
        self.ax.tick_params(labelleft=False)

        # แถบเทา = นอกช่วงที่ลายเซ็นเคยถูกคัดกรองและทดสอบ
        for a in (self.ax_ref, self.ax):
            a.axhspan(SPEED_LIM[0], VALIDATED_HZ[0], color=style.GRID, alpha=0.45, zorder=0)
            a.axhspan(VALIDATED_HZ[1], SPEED_LIM[1], color=style.GRID, alpha=0.45, zorder=0)
        self.ax.annotate(f"signatures were only screened at "
                         f"{VALIDATED_HZ[0]:.0f}-{VALIDATED_HZ[1]:.0f} Hz "
                         f"(white band)", xy=(0.995, 0.012), xycoords="axes fraction",
                         ha="right", va="bottom", fontsize=7.5, color=style.INK_SOFT)

        kw = dict(cmap="RdBu_r", norm=self.norm, edgecolors=style.INK,
                  linewidths=0.4, alpha=0.85, zorder=3)
        self.scat = self.ax.scatter([], [], c=[], **kw)
        self.scat_ref = self.ax_ref.scatter([], [], c=[], **kw)

        self.cax = self.fig.add_axes((0.874, 0.095, 0.015, 0.760))
        self.cb = self.fig.colorbar(self.scat, cax=self.cax)
        self.cb.ax.tick_params(labelsize=8)
        self.cb.outline.set_visible(False)

        panels = [
            ("ax_cls", (0.008, 0.665, 0.128, 0.215), "Fault class"),
            ("ax_ch", (0.008, 0.487, 0.128, 0.142), "Sensor channel"),
            ("ax_feat", (0.008, 0.225, 0.205, 0.205), "Feature"),
            ("ax_size", (0.008, 0.045, 0.128, 0.090), "Bubble size"),
        ]
        for name, rect, title in panels:
            a = self.fig.add_axes(rect)
            a.set_title(title, fontsize=9, loc="left", pad=6)
            a.set_facecolor(style.SURFACE)
            a.grid(False)
            a.set_xticks([])
            a.set_yticks([])
            for s in a.spines.values():
                s.set_visible(False)
            setattr(self, name, a)

        self.radio_cls = RadioButtons(self.ax_cls, [c.label for c in CATEGORIES],
                                      active=0, radio_props={"s": RADIO_SIZE})
        self.radio_cls.on_clicked(self._on_class)
        self.radio_ch = RadioButtons(self.ax_ch, list(CHANNELS),
                                     active=CHANNELS.index(self.channel),
                                     radio_props={"s": RADIO_SIZE})
        self.radio_ch.on_clicked(self._on_channel)
        # 12 feature เรียงสองคอลัมน์ ไม่งั้นแถวจะชิดกันจนกดยาก
        self.radio_feat = RadioButtons(
            self.ax_feat, list(self.features),
            active=self.features.index(self.feature),
            layout=(int(np.ceil(len(self.features) / 2)), 2),
            radio_props={"s": RADIO_SIZE})
        self.radio_feat.on_clicked(self._on_feature)
        for r in (self.radio_cls, self.radio_ch, self.radio_feat):
            for lbl in r.labels:
                lbl.set_fontsize(8.5)
            # วงกลมค่าเริ่มต้นโตแค่ 7 พิกเซล กดยากมาก จึงรับคลิกทั้งแถว
            row_clickable(r)

        ax_btn = self.fig.add_axes((0.008, 0.170, 0.072, 0.028))
        self.btn = Button(ax_btn, "signature", color=style.SURFACE,
                          hovercolor=style.GRID)
        self.btn.label.set_fontsize(8.5)
        self.btn.on_clicked(self._on_signature)

        self.t1 = self.fig.text(0.264, 0.980, "", fontsize=12.5, fontweight="bold",
                                color=style.INK, va="top")
        self.t2 = self.fig.text(0.264, 0.950, "", fontsize=8,
                                color=style.INK_SOFT, va="top")
        self.t3 = self.fig.text(0.264, 0.928, "", fontsize=8, va="top")
        self.t4 = self.fig.text(0.264, 0.906, "", fontsize=8, color="#b07500", va="top")
        self.pick_txt = self.fig.text(0.145, 0.165, "", fontsize=8,
                                      color=style.INK_SOFT, va="top")
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)

    # ---------- การตอบสนอง ----------

    def _set_radio(self, radio, index: int) -> None:
        """ตั้งปุ่มโดยไม่ให้ callback ของมันวาดซ้ำ ผู้เรียกต้องวาดเองทีเดียว"""
        self._mute = True
        radio.set_active(index)
        self._mute = False

    def _on_class(self, label: str) -> None:
        if self._mute:
            return
        self.cat = next(c for c in CATEGORIES if c.label == label)
        self._redraw()

    def _on_channel(self, label: str) -> None:
        if self._mute:
            return
        self.channel = label
        self._redraw()

    def _on_feature(self, label: str) -> None:
        if self._mute:
            return
        self.feature = label
        self._redraw()

    def _on_signature(self, _event) -> None:
        """กระโดดไปที่ช่องและ feature ที่เป็นลายเซ็นของคลาสที่เลือกอยู่"""
        sig = SIGNATURES[self.cat.label]
        if sig.status == "none" or sig.feature not in self.features:
            return
        self.channel = sig.channel
        self.feature = sig.feature
        self._set_radio(self.radio_ch, CHANNELS.index(sig.channel))
        self._set_radio(self.radio_feat, self.features.index(sig.feature))
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
        self.pick_txt.set_text(f"clicked:\n{p['rel']}\n{p['ratio']:.3g}x Normal "
                               f"({self.channel}.{self.feature})")
        self.fig.canvas.draw_idle()

    # ---------- การวาด ----------

    def _draw_bubbles(self, scat, p: pd.DataFrame, top: float, span: float) -> None:
        """พื้นที่วงแปรผันตรงกับค่า (ไม่ใช่รัศมี) เพราะสายตาคนอ่านพื้นที่ ไม่ใช่รัศมี

        ทั้งสองแกนใช้ ``top`` ตัวเดียวกัน ขนาดวงในแถบ normal จึงเทียบกับกราฟหลัก
        ได้ตรงๆ ถ้าแยกกันคิด วงของ normal จะโตเท่าวงที่ใหญ่ที่สุดของคลาสที่เสีย
        """
        scat.set_offsets(np.c_[p["x"], p["y"]] if len(p) else np.empty((0, 2)))
        # ส่งเป็น log10 ที่หารด้วย span แล้ว ค่าจึงอยู่ใน -1..1 เสมอ ดูเหตุผลที่
        # ต้องทำแบบนี้ในคำอธิบายของ _colorbar_ticks
        scat.set_array(np.clip(np.log10(p["ratio"].clip(lower=1e-12)),
                               -span, span) / span)
        scat.set_sizes(AREA_MIN + (AREA_MAX - AREA_MIN)
                       * (p["ratio"] / top).clip(lower=0, upper=1))

    def _redraw(self) -> None:
        p = self._select()
        ref = self._select_normal()
        self.points = p.reset_index(drop=True)
        self.ref_points = ref.reset_index(drop=True)
        sig = SIGNATURES[self.cat.label]
        top = max(float(p["ratio"].max()) if len(p) else 1.0,
                  float(ref["ratio"].max()) if len(ref) else 1.0)

        span = self._color_span()
        self._draw_bubbles(self.scat, p, top, span)
        self._draw_bubbles(self.scat_ref, ref, top, span)
        self._colorbar_ticks(span)

        if len(p):
            levels = sorted(p["x"].unique())
            pad = (max(levels) - min(levels)) * 0.12 or 1.0
            self.ax.set_xlim(min(levels) - pad, max(levels) + pad)
            self.ax.set_xticks(levels)
        self.ax_ref.set_ylim(*SPEED_LIM)
        self.ax.set_xlabel("Added mass (g)" if self.cat.unit == "g"
                           else "Misalignment offset (mm)")

        self._size_legend(top)
        self._titles(p, ref, top, sig)
        self.fig.canvas.draw_idle()

    def _colorbar_ticks(self, span: float) -> None:
        """เปลี่ยนเฉพาะข้อความของ tick ไม่เปลี่ยนช่วงของ norm

        **ห้ามเปลี่ยนช่วงของ norm ระหว่างใช้งาน** ไม่ว่าจะแก้ ``vmin``/``vmax``
        หรือใส่ norm ตัวใหม่ก็ตาม เพราะ colorbar จะอัปเดตตัวเองทันทีที่ norm
        เปลี่ยน และมีจังหวะหนึ่งที่กรอบของแกน colorbar สูงเป็นศูนย์
        matplotlib จึงหาร 1/0 ตอนสร้าง transform แล้วขึ้น
        ``RuntimeWarning: invalid value encountered in scalar multiply``
        (ไล่มาจาก spines.py 154 -> patches.py 760 -> transforms.py 2692)
        ภาพที่ได้ถูกต้องเพราะการวาดจริงเกิดหลังจากตั้งค่าครบแล้ว
        แต่คำเตือนจะโผล่ทุกครั้งที่สลับ feature ซึ่งน่ารำคาญและบังข้อความอื่น

        วิธีที่ใช้คือ **ตรึง norm ไว้ที่ -1 ถึง 1 ตลอดอายุโปรแกรม** แล้วหาร
        ค่าที่ส่งเข้าไปด้วย ``span`` ก่อน ตำแหน่ง tick จึงคงที่ เหลือแต่
        ข้อความที่เปลี่ยนตาม feature
        """
        ticks = np.linspace(-1.0, 1.0, 7)
        self.cb.set_ticks(list(ticks))
        self.cb.set_ticklabels([f"{10.0 ** (t * span):.3g}x" for t in ticks])
        self.cb.set_label(f"{FEATURE_INFO[self.feature][0]} vs Normal  (log scale)",
                          fontsize=8.5)

    def _titles(self, p, ref, top: float, sig) -> None:
        nice, meaning = FEATURE_INFO[self.feature]
        self.t1.set_text(f"{self.cat.label}  ·  {self.channel}  ·  {nice}")
        lo, hi = (ref["ratio"].min(), ref["ratio"].max()) if len(ref) else (np.nan,) * 2
        self.t2.set_text(
            f"{len(p)} files   |   {meaning}   |   largest here: {top:.3g}x   |   "
            f"Normal strip spans {lo:.2f}-{hi:.2f}x = how much a healthy machine "
            f"varies on its own")

        if sig.status == "none":
            self.t3.set_text("[none] no verified signature for this fault")
        else:
            hit = (self.channel == sig.channel) and (self.feature == sig.feature)
            self.t3.set_text(
                f"signature: {sig.channel}.{sig.feature}  ({sig.expected})"
                + ("   <-- you are looking at it" if hit
                   else "   |   press 'signature' to jump there"))
        self.t3.set_color(STATUS_COLOR[sig.status])
        self.t4.set_text(CHANNEL_NOTE.get(self.channel, ""))
        self.pick_txt.set_text("")

    def _size_legend(self, top: float) -> None:
        """วงตัวอย่างสามขนาด บอกว่าขนาดเท่านี้หมายถึงกี่เท่าในภาพที่กำลังดู"""
        self.ax_size.clear()
        # clear() ลบหัวเรื่องไปด้วย ต้องใส่กลับทุกครั้ง ไม่งั้นคำว่า Bubble size
        # จะหายไปตั้งแต่การวาดรอบที่สอง
        self.ax_size.set_title("Bubble size", fontsize=9, loc="left", pad=6)
        self.ax_size.set_xlim(0, 1)
        self.ax_size.set_ylim(0, 1)
        self.ax_size.set_xticks([])
        self.ax_size.set_yticks([])
        self.ax_size.grid(False)
        for frac, y in zip(SIZE_LEGEND_FRAC, (0.80, 0.48, 0.16)):
            area = AREA_MIN + (AREA_MAX - AREA_MIN) * frac
            self.ax_size.scatter([0.22], [y], s=area, facecolor="none",
                                 edgecolor=style.INK_SOFT, linewidths=0.7)
            self.ax_size.text(0.52, y, f"{top * frac:.3g}x", fontsize=8,
                              va="center", color=style.INK_SOFT)


def main() -> int:
    argparse.ArgumentParser(description="bubble plot ของ feature ทั้ง dataset"
                            ).parse_args()
    if plt.get_backend().lower() == "agg":
        print("matplotlib ใช้ backend 'agg' ซึ่งเปิดหน้าต่างไม่ได้ "
              "ต้องรันบนเครื่องที่มีจอ", file=sys.stderr)
        return 1
    try:
        tab, feats = load_table()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    style.apply()
    app = BubbleGrid(tab, feats)      # ต้องเก็บตัวแปรไว้ ดูคำอธิบายใน _build
    plt.show()
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

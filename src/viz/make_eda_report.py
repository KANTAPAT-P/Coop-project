"""สร้างชุดกราฟสำรวจข้อมูล MAFAULDA ลง reports/eda/

รัน:
    python src/viz/make_eda_report.py
    python src/viz/make_eda_report.py --target-hz 45 --n-sample 15

**หลักการที่ยึดตลอดทั้งไฟล์นี้**

1. *คุมความเร็วรอบก่อนเสมอ* แอมพลิจูดการสั่นโตตามความเร็วรอบยกกำลังสอง
   ถ้าเอา normal ที่ 15 Hz ไปเทียบกับ imbalance ที่ 55 Hz แล้วบอกว่า
   "imbalance สั่นแรงกว่า" ก็เท่ากับไม่ได้วัดอะไรเลยนอกจากความเร็ว
   ทุกกราฟจึงเลือกไฟล์ที่ความเร็วใกล้ ``--target-hz`` ที่สุดของแต่ละคลาส
   แล้วพิมพ์ความเร็วจริงกำกับไว้บนหัวแผงให้ตรวจสอบได้

2. *ใช้ bearing fault ที่มวลถ่วง 0 g* เพราะไฟล์ที่มวล > 0 g มี imbalance
   ผสมอยู่ ถ้าเอามาพล็อตจะเห็นพีคใหญ่ที่ 1x แล้วเข้าใจผิดว่าเป็นผลของ
   ความเสียหายตลับลูกปืน ทั้งที่เป็นผลของมวลถ่วงที่คนทำ dataset เติมเข้าไปเอง

3. *ใช้แกน y ร่วมกันทุกแผงในรูปเดียวกัน* ถ้าปล่อยให้แต่ละแผง autoscale
   สัญญาณที่เล็กกว่าสิบเท่าจะดูใหญ่เท่ากัน ซึ่งเป็นการโกหกด้วยกราฟ
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
from src.features import basic, spectral  # noqa: E402
from src.paths import bearing_coefficients, repo_root, sampling_rate  # noqa: E402
from src.viz import style  # noqa: E402

FS = sampling_rate()
OUT = repo_root() / "reports" / "eda"

# ช่องที่ใช้เป็นหลัก เลือก underhang radial เพราะเป็นทิศที่ imbalance และ
# misalignment แสดงตัวชัดที่สุด และเป็นช่องที่ระดับสัญญาณปกติ
# (ไม่ใช้ o_radial ที่สัญญาณต่ำผิดปกติ และไม่ใช้ mic ที่สเกลเพี้ยนในคลาส imbalance)
MAIN_CH = "u_radial"

# ตลับลูกปืนแต่ละฝั่งต้องฟังจากเซ็นเซอร์ฝั่งเดียวกัน แรงกระแทกความถี่สูง
# ถูกดูดซับไปมากระหว่างทางถ้าวัดจากอีกฝั่งของเพลา
SIDE_CH = {"underhang": "u_radial", "overhang": "o_tang"}

# MAFAULDA ไม่มี inner race จึงไม่แสดง BPFI
BEARING_MARKS = ["FTF", "BSF", "BPFO"]

# อัตราส่วน ความเร็วจริง/ชื่อไฟล์ มัธยฐานของทั้ง dataset
# ใช้เป็นค่าประมาณสำรองเมื่อ tachometer ของไฟล์นั้นวัดไม่ผ่านเกณฑ์
SLIP_RATIO = 0.9767

# มวลถ่วงของ imbalance ที่ใช้เป็นตัวแทนคลาสในรูปที่ 01, 02
# ตรึงไว้เพื่อให้รูปซ้ำได้ เลือก 35 g ซึ่งเป็นค่าสูงสุด เพราะเป็นเคสที่เห็นผล
# ชัดที่สุดในสัญญาณดิบ ข้อควรรู้: กลุ่ม 35 g มีข้อมูลถึงแค่ 56.7 Hz
# ถ้าสั่ง --target-hz สูงกว่านั้นจะได้ไฟล์ที่ความเร็วห่างจากเป้าหมาย
IMBALANCE_MASS_G = 35

# ป้ายแกน X สองแบบที่ห้ามสลับกัน
#
# FFT ธรรมดาวัดว่า "เซ็นเซอร์สั่นเร็วแค่ไหน" ส่วน FFT ของ envelope วัดว่า
# "ความดังของการสั่นความถี่สูงเต้นเร็วแค่ไหน" — คนละเรื่องกันโดยสิ้นเชิง
# พีคที่ 90 Hz ใน envelope spectrum ไม่ได้แปลว่ามีอะไรสั่นที่ 90 Hz
# แต่แปลว่าการสั่นที่ 2-5 kHz ดังขึ้นและเบาลง 90 ครั้งต่อวินาที
#
# เคยเขียนป้ายว่า "Frequency (Hz)" เหมือนกันทั้งสองแบบ ซึ่งทำให้เข้าใจผิดได้ง่าย
# โดยเฉพาะในรูปที่มีทั้งสองแบบอยู่คนละแถวของรูปเดียวกัน
XLABEL_VIBRATION = "Vibration frequency (Hz)"
XLABEL_ENVELOPE = "Impact repeat rate (Hz)"


def _rot(row: pd.Series) -> float:
    """ความเร็วรอบที่ควรใช้คำนวณความถี่ความเสียหาย

    ใช้ค่าที่วัดจาก tachometer เสมอเมื่อมี เพราะชื่อไฟล์คือความถี่ที่**ตั้งไว้ที่ไดรฟ์**
    ซึ่งสูงกว่าความเร็วเพลาจริงราว 2.3% ถ้าใช้ชื่อไฟล์ เส้นบอกตำแหน่ง BPFO
    จะวางผิดไปราว 10 ช่องความถี่ของ FFT

    ตัว tachometer เองก็วัดพลาดได้ในไฟล์ที่เครื่องสั่นแรง จึงต้องเช็ก ``tach_ok``
    ก่อน ถ้าไม่ผ่านให้ถอยไปใช้ชื่อไฟล์คูณอัตราส่วน slip แทน ใช้ตรรกะเดียวกับ
    ``mafaulda.speed_hz()`` เพื่อไม่ให้มีสองมาตรฐานในโปรเจกต์
    """
    return float(mf.speed_hz(row.to_frame().T, fallback_ratio=SLIP_RATIO).iloc[0])


def _panel_title(row: pd.Series) -> str:
    label = mf.CLASS_LABELS[row["cls"]]
    bits = [label]
    if row["subclass"]:
        bits.append(str(row["subclass"]))
    rot = _rot(row)
    return (f"{' · '.join(bits)}\n{rot:.2f} Hz ({rot * 60:.0f} rpm)"
            f"   [set {row['rot_hz']:.2f}]")


def _select_one_per_class(index: pd.DataFrame, target_hz: float) -> dict[str, pd.Series]:
    """เลือกไฟล์ตัวแทนคลาสละหนึ่งไฟล์ ที่ความเร็วใกล้เป้าหมายที่สุด

    **ต้องตรึงมวลถ่วงของ imbalance ไว้ด้วย** ไม่ใช่ปล่อยให้เลือกจากทุกมวล
    ไม่งั้นไฟล์ที่ถูกเลือกจะเปลี่ยนไปมาทุกครั้งที่เกณฑ์การจับคู่ความเร็วขยับ
    (เคยได้ 35g แล้วเป็น 20g แล้วเป็น 25g มาแล้ว) ซึ่งทำให้คำอธิบายในรายงาน
    ไม่ตรงกับรูปโดยไม่มีใครรู้ตัว
    """
    picks = {}
    for cls in mf.CLASS_ORDER:
        # bearing fault เอาเฉพาะ 0 g เพื่อไม่ให้ imbalance ปนเข้ามา
        mass = 0 if cls in ("underhang", "overhang") else None
        sub = "outer_race" if cls in ("underhang", "overhang") else None
        if cls == "imbalance":
            mass = IMBALANCE_MASS_G
        picks[cls] = mf.pick_matched_speed(index, target_hz, cls, subclass=sub, mass_g=mass)
    return picks


# --------------------------------------------------------------------------
# รูปที่ 1 — สัญญาณดิบในโดเมนเวลา
# --------------------------------------------------------------------------

def fig_raw_waveform(picks: dict[str, pd.Series], signals: dict[str, np.ndarray],
                     window_s: float = 0.08) -> Path:
    n = int(window_s * FS)
    t = np.arange(n) / FS * 1000.0          # ms อ่านง่ายกว่าวินาทีที่ช่วงสั้นๆ
    ref = signals["normal"][:n] - signals["normal"][:n].mean()

    ymax = max(np.abs(s[:n] - s[:n].mean()).max() for s in signals.values()) * 1.05

    fig, axes = plt.subplots(3, 2, figsize=(11, 7.5), sharex=True, sharey=True)
    for ax, cls in zip(axes.ravel(), mf.CLASS_ORDER):
        sig = signals[cls][:n]
        sig = sig - sig.mean()

        if cls != "normal":
            ax.plot(t, ref, color=style.REFERENCE, linewidth=0.6, zorder=1,
                    label="Normal (reference)")
        ax.plot(t, sig, color=style.color(cls), linewidth=0.7, zorder=2)
        ax.set_title(_panel_title(picks[cls]), loc="left")
        ax.set_ylim(-ymax, ymax)
        if cls != "normal":
            ax.legend(loc="upper right", fontsize=7)

    for ax in axes[-1]:
        ax.set_xlabel("Time (ms)")
    for ax in axes[:, 0]:
        ax.set_ylabel(f"{MAIN_CH} (g)")

    style.finish(
        fig,
        "Raw vibration, same speed, same scale",
        f"Channel {MAIN_CH} · {window_s * 1000:.0f} ms window · bearing faults at 0 g added mass · "
        "grey line behind each panel is Normal",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = OUT / "01-raw-waveform.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# รูปที่ 2 — สเปกตรัมย่านต่ำ
# --------------------------------------------------------------------------

def fig_spectrum(picks: dict[str, pd.Series], signals: dict[str, np.ndarray],
                 fmax: float = 400.0) -> Path:
    spec = {cls: spectral.spectrum(sig, FS) for cls, sig in signals.items()}
    fref, mref = spec["normal"]
    mask_ref = fref <= fmax

    ymax = max(m[f <= fmax][1:].max() for f, m in spec.values()) * 2

    fig, axes = plt.subplots(3, 2, figsize=(11, 7.5), sharex=True, sharey=True)
    for ax, cls in zip(axes.ravel(), mf.CLASS_ORDER):
        f, m = spec[cls]
        mask = f <= fmax
        rot = _rot(picks[cls])

        if cls != "normal":
            ax.plot(fref[mask_ref], mref[mask_ref], color=style.REFERENCE,
                    linewidth=0.6, zorder=1, label="Normal (reference)")
        ax.plot(f[mask], m[mask], color=style.color(cls), linewidth=0.9, zorder=2)

        ax.set_yscale("log")
        ax.set_ylim(1e-4, ymax)
        ax.set_xlim(0, fmax)
        style.annotate_lines(ax, {f"{k}x": rot * k for k in (1, 2, 3)})
        ax.set_title(_panel_title(picks[cls]), loc="left")
        if cls != "normal":
            ax.legend(loc="upper right", fontsize=7)

    for ax in axes[-1]:
        ax.set_xlabel(XLABEL_VIBRATION)
    for ax in axes[:, 0]:
        ax.set_ylabel("Amplitude (g)")

    style.finish(
        fig,
        "Low-frequency spectrum: where imbalance and misalignment live",
        f"Channel {MAIN_CH} · log amplitude · dashed lines mark 1x, 2x, 3x the shaft speed",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = OUT / "02-spectrum-low.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# รูปที่ 3 — envelope spectrum ของความเสียหายตลับลูกปืนทั้ง 6 ชนิด
# --------------------------------------------------------------------------

def fig_envelope(index: pd.DataFrame, target_hz: float, fmax: float = 250.0) -> Path:
    coeffs = bearing_coefficients()
    faults = ["outer_race", "ball_fault", "cage_fault"]

    cases: list[tuple[str, pd.Series, str]] = [
        ("normal", mf.pick_matched_speed(index, target_hz, "normal"), SIDE_CH["underhang"]),
    ]
    for side in ("underhang", "overhang"):
        for fault in faults:
            row = mf.pick_matched_speed(index, target_hz, side, subclass=fault, mass_g=0)
            cases.append((side, row, SIDE_CH[side]))

    results = []
    for _, row, ch in cases:
        sig = mf.load(row["path"], [ch])[ch].to_numpy()
        f, m = spectral.envelope_spectrum(sig, FS)
        results.append((f, m))

    ymax = max(m[(f > 2) & (f <= fmax)].max() for f, m in results) * 1.15

    # เรียง normal ไว้แผงแรกเป็นฐานเปรียบเทียบ แล้วไล่ underhang 3 ชนิด
    # ตามด้วย overhang 3 ชนิด แผงที่เหลือซ่อนทิ้ง
    fig, axes = plt.subplots(4, 2, figsize=(11.5, 10), sharex=True, sharey=True)
    flat = axes.ravel()

    for ax, (side, row, ch), (f, m) in zip(flat, cases, results):
        rot = _rot(row)
        marks = {k: v for k, v in spectral.fault_frequencies(rot, coeffs).items()
                 if k in BEARING_MARKS}

        mask = f <= fmax
        ax.plot(f[mask], m[mask], color=style.color(side), linewidth=0.9, zorder=2)
        ax.set_ylim(0, ymax)
        ax.set_xlim(0, fmax)
        style.annotate_lines(ax, marks)

        label = "Normal" if side == "normal" else f"{mf.CLASS_LABELS[side]} · {row['subclass']}"
        ax.set_title(f"{label}   [{ch}]\n{rot:.2f} Hz ({rot * 60:.0f} rpm)", loc="left")

    for ax in flat[len(cases):]:
        ax.set_visible(False)
    for ax in flat[max(0, len(cases) - 2):len(cases)]:
        ax.set_xlabel(XLABEL_ENVELOPE)
    for ax in axes[:, 0]:
        ax.set_ylabel("Envelope amplitude (g)")

    style.finish(
        fig,
        "Envelope spectrum: the only view where bearing faults show up",
        f"Band-pass {spectral.DEFAULT_BAND[0]:.0f}-{spectral.DEFAULT_BAND[1]:.0f} Hz then Hilbert · "
        "all at 0 g added mass · dashed lines are the theoretical FTF / BSF / BPFO for that speed",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = OUT / "03-envelope-spectrum.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------
# รูปที่ 4 — การกระจายของ feature โดเมนเวลา
# --------------------------------------------------------------------------

def fig_features(index: pd.DataFrame, n_sample: int, hz_range: tuple[float, float]) -> tuple[Path, pd.DataFrame]:
    rows = []
    for cls in mf.CLASS_ORDER:
        # bearing fault คุมที่ 0 g เหมือนรูปอื่น ส่วน imbalance ปล่อยทุกมวล
        # เพราะมวลถ่วงคือตัวความเสียหายเองของคลาสนั้น
        mass = 0 if cls in ("underhang", "overhang") else None
        sel = mf.sample_files(index, cls, n_sample, hz_range=hz_range, mass_g=mass)
        for _, r in sel.iterrows():
            sig = mf.load(r["path"], [MAIN_CH])[MAIN_CH].to_numpy()
            rows.append({"cls": cls, "rot_hz": r["rot_hz"], "rel": r["rel"], **basic.compute(sig)})

    feat = pd.DataFrame(rows)

    show = ["rms", "crest_factor", "kurtosis"]
    titles = {
        "rms": "RMS — overall vibration energy",
        "crest_factor": "Crest factor — how spiky",
        "kurtosis": "Kurtosis — how heavy the tails",
    }

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6))
    for ax, feature in zip(axes, show):
        data = [feat.loc[feat["cls"] == c, feature].to_numpy() for c in mf.CLASS_ORDER]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=False,
                        medianprops=dict(color=style.INK, linewidth=1.4),
                        whiskerprops=dict(color=style.INK_SOFT, linewidth=0.8),
                        capprops=dict(color=style.INK_SOFT, linewidth=0.8))
        for patch, cls in zip(bp["boxes"], mf.CLASS_ORDER):
            patch.set_facecolor(style.color(cls))
            patch.set_alpha(0.55)
            patch.set_edgecolor(style.color(cls))
            patch.set_linewidth(1.2)

        # จุดดิบทับลงไปด้วย เพราะ boxplot จาก 10 กว่าจุดซ่อนความจริงได้ง่าย
        for i, (cls, vals) in enumerate(zip(mf.CLASS_ORDER, data), start=1):
            jitter = np.random.default_rng(i).normal(0, 0.055, len(vals))
            ax.scatter(i + jitter, vals, s=9, color=style.INK, alpha=0.45,
                       zorder=3, linewidths=0)

        ax.set_title(titles[feature], loc="left")
        ax.set_xticks(range(1, len(mf.CLASS_ORDER) + 1))
        ax.set_xticklabels([mf.CLASS_LABELS[c].replace(" ", "\n") for c in mf.CLASS_ORDER],
                           fontsize=7.5)

    axes[2].axhline(3, color=style.MARKER, linestyle=(0, (3, 3)), linewidth=0.9)
    axes[2].annotate("3 = Gaussian noise", xy=(0.02, 3), xycoords=("axes fraction", "data"),
                     xytext=(0, 4), textcoords="offset points",
                     fontsize=7, color=style.MARKER)

    style.finish(
        fig,
        "Time-domain features by class",
        f"Channel {MAIN_CH} · up to {n_sample} files per class, "
        f"shaft speed restricted to {hz_range[0]:.0f}-{hz_range[1]:.0f} Hz · "
        "bearing faults at 0 g · dots are individual files",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = OUT / "04-feature-distribution.png"
    fig.savefig(path)
    plt.close(fig)
    return path, feat


# --------------------------------------------------------------------------
# รูปที่ 5 — กับดัก imbalance ปนใน bearing fault
# --------------------------------------------------------------------------

def fig_imbalance_trap(index: pd.DataFrame, target_hz: float) -> Path:
    coeffs = bearing_coefficients()
    cases = [
        ("Normal", mf.pick_matched_speed(index, target_hz, "normal"), "normal"),
        ("Imbalance 35 g", mf.pick_matched_speed(index, target_hz, "imbalance", mass_g=35), "imbalance"),
        ("Outer race, 0 g", mf.pick_matched_speed(index, target_hz, "underhang", "outer_race", 0), "underhang"),
        ("Outer race, 35 g", mf.pick_matched_speed(index, target_hz, "underhang", "outer_race", 35), "underhang"),
    ]

    loaded = []
    for label, row, cls in cases:
        sig = mf.load(row["path"], [MAIN_CH])[MAIN_CH].to_numpy()
        loaded.append((label, row, cls, spectral.spectrum(sig, FS),
                       spectral.envelope_spectrum(sig, FS)))

    fmax_lo, fmax_env = 400.0, 250.0
    ymax_lo = max(m[(f > 2) & (f <= fmax_lo)].max() for _, _, _, (f, m), _ in loaded) * 2
    ymax_env = max(m[(f > 2) & (f <= fmax_env)].max() for _, _, _, _, (f, m) in loaded) * 1.15

    fig, axes = plt.subplots(2, 4, figsize=(14, 6.6), sharey="row")
    for col, (label, row, cls, (f1, m1), (f2, m2)) in enumerate(loaded):
        rot = _rot(row)

        ax = axes[0, col]
        mask = f1 <= fmax_lo
        ax.plot(f1[mask], m1[mask], color=style.color(cls), linewidth=0.9)
        ax.set_yscale("log")
        ax.set_ylim(1e-4, ymax_lo)
        ax.set_xlim(0, fmax_lo)
        style.annotate_lines(ax, {f"{k}x": rot * k for k in (1, 2)})
        ax.set_title(f"{label}\n{rot:.2f} Hz", loc="left")
        # แถวบนต้องมีป้ายแกนของตัวเอง ห้ามให้ใช้ป้ายร่วมกับแถวล่าง
        # เพราะสองแถวนี้แกน X คนละความหมายกัน
        ax.set_xlabel(XLABEL_VIBRATION)

        ax = axes[1, col]
        marks = {k: v for k, v in spectral.fault_frequencies(rot, coeffs).items()
                 if k in BEARING_MARKS}
        band = (f2 > 2) & (f2 <= fmax_env)
        ax.plot(f2[band], m2[band], color=style.color(cls), linewidth=0.9)
        ax.set_ylim(0, ymax_env)
        ax.set_xlim(0, fmax_env)
        style.annotate_lines(ax, marks)
        ax.set_xlabel(XLABEL_ENVELOPE)

        # ระดับพื้นของ envelope คือสิ่งที่แยกความเสียหายตลับลูกปืนออกได้จริง
        # ไม่ใช่พีคที่ BPFO เพราะพีคนั้นทับกับฮาร์มอนิกที่ 3 ของความเร็วรอบ
        floor = float(np.median(m2[band]))
        ax.annotate(
            f"envelope floor\n{floor * 1000:.2f} mg",
            xy=(0.97, 0.93), xycoords="axes fraction", ha="right", va="top",
            fontsize=7.5, color=style.INK,
        )

    axes[0, 0].set_ylabel("Plain FFT\namplitude (g)")
    axes[1, 0].set_ylabel("Envelope FFT\namplitude (g)")

    style.finish(
        fig,
        "Added mass makes a bearing fault look like imbalance - and BPFO cannot rescue you",
        f"Channel {MAIN_CH} · top row plain spectrum, bottom row envelope spectrum · "
        "BPFO is 2.998x shaft speed, which a 4.88 s record cannot separate from the 3rd shaft "
        "harmonic, so imbalance shows a peak there too · compare the envelope floor numbers instead",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = OUT / "05-imbalance-trap.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_envelope_floor(index: pd.DataFrame, n_sample: int,
                       hz_range: tuple[float, float]) -> tuple[Path, pd.DataFrame]:
    """ทดสอบว่า "ระดับพื้นของ envelope" แยก bearing fault ออกได้จริงไหม

    รูปที่ 5 ชี้ว่าพีคที่ BPFO ใช้เป็นหลักฐานไม่ได้ เพราะทับกับฮาร์มอนิกที่ 3
    ของความเร็วรอบ คำถามถัดมาคือแล้วอะไรใช้ได้ รูปนี้ทดสอบผู้สมัครสองตัว
    ด้วยไฟล์หลายสิบไฟล์ ไม่ใช่ไฟล์เดียวเหมือนรูปที่ 5

        envelope_floor  มัธยฐานของ envelope spectrum ทั้งแถบ = เสียงกระแทกแบบสุ่ม
        band_kurtosis   kurtosis ของสัญญาณหลัง bandpass 2-5 kHz = ความแหลมของการกระแทก

    ทั้งสองตัวไม่ขึ้นกับพีคที่ความถี่ใดความถี่หนึ่ง จึงไม่โดนปัญหา BPFO ทับ 3x
    """
    groups = [
        ("Normal", "normal", None, None),
        ("Imbalance 35 g", "imbalance", None, 35),
        ("Outer race 0 g", "underhang", "outer_race", 0),
        ("Outer race 35 g", "underhang", "outer_race", 35),
        ("Ball fault 0 g", "underhang", "ball_fault", 0),
        ("Cage fault 0 g", "underhang", "cage_fault", 0),
    ]

    rows = []
    for label, cls, sub, mass in groups:
        sel = index[index["cls"] == cls]
        if sub is not None:
            sel = sel[sel["subclass"] == sub]
        if mass is not None:
            sel = sel[sel["mass_g"] == mass]
        sel = sel[sel["rot_hz"].between(*hz_range)]
        sel = sel.sample(n=min(n_sample, len(sel)), random_state=0)

        for _, r in sel.iterrows():
            sig = mf.load(r["path"], [MAIN_CH])[MAIN_CH].to_numpy()
            f, m = spectral.envelope_spectrum(sig, FS)
            band = (f > 2) & (f <= 250)
            filt = spectral.bandpass(sig, FS, *spectral.DEFAULT_BAND)
            rows.append({
                "group": label,
                "cls": cls,
                "rot_hz": r["rot_hz"],
                "rel": r["rel"],
                "envelope_floor_mg": float(np.median(m[band])) * 1000,
                "band_kurtosis": basic.kurtosis(filt),
            })

    ef = pd.DataFrame(rows)
    labels = [g[0] for g in groups]
    colors = [style.color(g[1]) for g in groups]

    panels = [
        ("envelope_floor_mg", "Envelope floor (mg)", "Broadband envelope level"),
        ("band_kurtosis", "Kurtosis of 2-5 kHz band", "Impulsiveness inside the resonance band"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, (col, ylab, title) in zip(axes, panels):
        data = [ef.loc[ef["group"] == g, col].to_numpy() for g in labels]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=False,
                        medianprops=dict(color=style.INK, linewidth=1.4),
                        whiskerprops=dict(color=style.INK_SOFT, linewidth=0.8),
                        capprops=dict(color=style.INK_SOFT, linewidth=0.8))
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.55)
            patch.set_edgecolor(c)
            patch.set_linewidth(1.2)
        for i, vals in enumerate(data, start=1):
            jitter = np.random.default_rng(i).normal(0, 0.055, len(vals))
            ax.scatter(i + jitter, vals, s=10, color=style.INK, alpha=0.45,
                       zorder=3, linewidths=0)

        ax.set_title(title, loc="left")
        ax.set_ylabel(ylab)
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels([l.replace(" ", "\n") for l in labels], fontsize=7.5)

    # ขีดเส้นค่ามัธยฐานของ normal ไว้เป็นฐานเปรียบเทียบในทั้งสองแผง
    for ax, (col, _, _) in zip(axes, panels):
        base = ef.loc[ef["group"] == "Normal", col].median()
        # ไม่เขียนป้ายทับบนกราฟ เพราะเส้นนี้พาดผ่านกล่อง Normal พอดี
        # คำอธิบายอยู่ในหัวรูปแทน
        ax.axhline(base, color=style.MARKER, linestyle=(0, (3, 3)), linewidth=0.9)

    style.finish(
        fig,
        "Two features that do not depend on any single fault frequency",
        f"Channel {MAIN_CH} · up to {n_sample} files per group, shaft speed "
        f"{hz_range[0]:.0f}-{hz_range[1]:.0f} Hz · dots are individual files · "
        "dashed line is the Normal median",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = OUT / "06-envelope-floor.png"
    fig.savefig(path)
    plt.close(fig)
    return path, ef


def fig_envelope_explained(index: pd.DataFrame, target_hz: float) -> Path:
    """อธิบายว่า envelope คืออะไร และแกนความถี่ของมันหมายถึงอะไร

    รูปนี้มีไว้แก้ความสับสนข้อเดียวที่สำคัญที่สุดของทั้งชุด

        แกน X ของ FFT ธรรมดา   = เซ็นเซอร์สั่นเร็วแค่ไหน
        แกน X ของ envelope FFT = "ความดัง" ของการสั่นความถี่สูง เต้นเร็วแค่ไหน

    สองอันนี้เป็นคนละเรื่องกันโดยสิ้นเชิง พีคที่ 90 Hz ใน envelope spectrum
    ไม่ได้แปลว่ามีอะไรสั่นที่ 90 Hz แต่แปลว่าการสั่นที่ 2-5 kHz **ดังขึ้นและเบาลง
    90 ครั้งต่อวินาที** ตัวคลื่นยังสั่นที่ 2-5 kHz เหมือนเดิม
    """
    # เลือกไฟล์ที่พีค BPFO เด่นที่สุดเทียบกับพื้น ไม่ใช่ไฟล์ที่ความเร็วใกล้เป้าหมายที่สุด
    # เพราะรูปนี้มีไว้**สอนวิธี** ไม่ได้มีไว้เทียบคลาส จึงควรใช้ตัวอย่างที่เห็นชัดที่สุด
    # ยังคงเป็นมวลถ่วง 0 g เหมือนเดิม ไม่ได้เลือกเคสที่ถูกขยายด้วย imbalance
    cand = index[(index["cls"] == "underhang") & (index["subclass"] == "outer_race")
                 & (index["mass_g"] == 0)]
    cand = cand[cand["rot_hz"].between(target_hz - 6, target_hz + 6)]
    best, best_score = None, -np.inf
    for _, cr in cand.iterrows():
        r_hz = _rot(cr)
        sig = mf.load(cr["path"], [MAIN_CH])[MAIN_CH].to_numpy()
        fe, me = spectral.envelope_spectrum(sig, FS)
        m_band = (fe > 2) & (fe <= 250)
        score = spectral.peak_near(fe, me, r_hz * bearing_coefficients()["BPFO"])[1] \
            / float(np.median(me[m_band]))
        if score > best_score:
            best, best_score = cr, score

    row = best
    rot = _rot(row)
    bpfo = rot * bearing_coefficients()["BPFO"]
    period_ms = 1000.0 / bpfo

    x = mf.load(row["path"], [MAIN_CH])[MAIN_CH].to_numpy()
    band = spectral.bandpass(x, FS, *spectral.DEFAULT_BAND)
    env = spectral.envelope(x, FS, spectral.DEFAULT_BAND)

    fig, axes = plt.subplots(4, 1, figsize=(11, 10.5))
    c = style.color("underhang")

    # A — สัญญาณดิบ 60 ms
    n = int(0.06 * FS)
    t = np.arange(n) / FS * 1000
    axes[0].plot(t, x[:n] - x[:n].mean(), color=style.INK_SOFT, linewidth=0.6)
    axes[0].set_title("A. Raw signal - every frequency mixed together, impacts are invisible", loc="left")
    axes[0].set_ylabel(f"{MAIN_CH} (g)")

    # B — หลัง bandpass ซูมให้เห็นคลื่นความถี่สูงจริงๆ
    n2 = int(0.003 * FS)
    t2 = np.arange(n2) / FS * 1000
    f_b, m_b = spectral.spectrum(band, FS)
    ring = f_b[np.argmax(m_b)]
    axes[1].plot(t2, band[:n2], color=c, linewidth=0.9)
    axes[1].set_title(
        f"B. Band-passed {spectral.DEFAULT_BAND[0]:.0f}-{spectral.DEFAULT_BAND[1]:.0f} Hz, "
        f"zoomed to 3 ms - a fast wave near {ring:.0f} Hz: the structure ringing",
        loc="left")
    axes[1].set_ylabel("bandpassed (g)")

    # C — envelope คือเส้นขอบ
    axes[2].plot(t, band[:n], color=c, linewidth=0.5, alpha=0.55, label="2-5 kHz wave")
    axes[2].plot(t, env[:n], color=style.INK, linewidth=1.6, label="envelope (the outline)")
    for k in range(1, int(60 / period_ms) + 1):
        axes[2].axvline(k * period_ms, color=style.MARKER, linestyle=(0, (3, 3)),
                        linewidth=0.8, alpha=0.8, zorder=0)
    axes[2].set_title(
        f"C. The envelope is that wave's outline - it bulges every {period_ms:.1f} ms, "
        f"matching the dashed 1/BPFO spacing",
        loc="left")
    axes[2].set_ylabel("g")
    axes[2].set_xlabel("Time (ms)")
    axes[2].legend(loc="lower left", fontsize=8, ncol=2)

    # D — FFT ของ envelope
    f_e, m_e = spectral.envelope_spectrum(x, FS)
    mask = f_e <= 250
    axes[3].plot(f_e[mask], m_e[mask], color=c, linewidth=0.9)
    style.annotate_lines(axes[3], {"BPFO": bpfo, "2xBPFO": bpfo * 2})
    axes[3].set_xlim(0, 250)
    axes[3].set_title(
        "D. FFT of that outline - a peak lands on BPFO because the bulges are periodic",
        loc="left")
    axes[3].set_ylabel("envelope amplitude (g)")
    axes[3].set_xlabel(f"{XLABEL_ENVELOPE} - NOT how fast the sensor vibrates")

    style.finish(
        fig,
        "How envelope analysis works",
        f"{row['rel']} · {MAIN_CH} · shaft {rot:.2f} Hz · BPFO = {bpfo:.1f} Hz · "
        f"clearest outer-race example at 0 g added mass (BPFO peak {best_score:.1f}x the floor)",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = OUT / "07-envelope-explained.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="สร้างกราฟสำรวจข้อมูล MAFAULDA")
    ap.add_argument("--target-hz", type=float, default=30.0,
                    help="ความเร็วรอบที่ใช้เทียบข้ามคลาส (Hz)")
    ap.add_argument("--n-sample", type=int, default=10,
                    help="จำนวนไฟล์ต่อคลาสสำหรับกราฟ feature")
    ap.add_argument("--hz-window", type=float, default=6.0,
                    help="ความกว้างครึ่งหนึ่งของช่วงความเร็วในกราฟ feature (Hz)")
    args = ap.parse_args()

    style.apply()
    OUT.mkdir(parents=True, exist_ok=True)

    index = mf.build_index()
    print(f"ดัชนี {len(index)} ไฟล์")

    picks = _select_one_per_class(index, args.target_hz)
    print(f"\nไฟล์ตัวแทนที่เลือก (เป้าหมาย {args.target_hz} Hz)")
    for cls, row in picks.items():
        print(f"  {mf.CLASS_LABELS[cls]:<22} วัดได้ {_rot(row):>7.3f} Hz "
              f"(ตั้งไว้ {row['rot_hz']:>7.3f})   {row['rel']}")

    signals = {cls: mf.load(row["path"], [MAIN_CH])[MAIN_CH].to_numpy()
               for cls, row in picks.items()}

    print("\nกำลังสร้างกราฟ")
    made = [
        fig_raw_waveform(picks, signals),
        fig_spectrum(picks, signals),
        fig_envelope(index, args.target_hz),
    ]
    hz_range = (args.target_hz - args.hz_window, args.target_hz + args.hz_window)
    feat_path, feat = fig_features(index, args.n_sample, hz_range)
    made.append(feat_path)
    made.append(fig_imbalance_trap(index, args.target_hz))
    floor_path, ef = fig_envelope_floor(index, args.n_sample, hz_range)
    made.append(floor_path)
    made.append(fig_envelope_explained(index, args.target_hz))

    out_csv = repo_root() / "data" / "processed"
    out_csv.mkdir(parents=True, exist_ok=True)
    feat.to_csv(out_csv / "eda_features.csv", index=False)
    ef.to_csv(out_csv / "eda_envelope_floor.csv", index=False)

    for p in made:
        print(f"  {p.relative_to(repo_root())}")

    print("\nสรุป feature โดเมนเวลา (median ต่อคลาส)")
    print(feat.groupby("cls")[basic.FEATURE_NAMES].median().round(3))

    print("\nสรุป envelope floor และ band kurtosis (median ต่อกลุ่ม)")
    summary = (ef.groupby("group", sort=False)[["envelope_floor_mg", "band_kurtosis"]]
                 .agg(["median", "min", "max", "count"]).round(3))
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""กราฟที่อาจารย์ขอ — เส้นเกณฑ์ ปกติเทียบผิดปกติ และแนวโน้มรายวัน

สร้างสองไฟล์ใน `reports/trend/`

* `01-threshold.png` — คะแนนสุขภาพตามเวลา พร้อม**เส้นเกณฑ์** แถบปกติ
  และ**วงบริเวณที่ผิดปกติ** ซึ่งคือสิ่งที่อาจารย์อยากเห็น
* `02-daily-trend.png` — จำนวนการเตือนรายวัน เทียบเครื่องที่เสื่อมสภาพ
  กับเครื่องที่ปกติ พร้อมผลการทดสอบ Mann-Kendall

## ⚠️ เส้นเวลานี้ประกอบขึ้น ไม่ใช่การเสื่อมสภาพที่วัดได้จริง

**MAFAULDA ไม่มีข้อมูล run-to-failure เลย** มีแต่สภาวะคงที่ที่ระดับความรุนแรง
ต่างๆ เส้นเวลาจึงประกอบจากการไล่ระดับความรุนแรงที่มีอยู่

    วันที่ 1-12   normal
    วันที่ 13-21  h-misalignment 0.5 mm
    วันที่ 22-30  h-misalignment 1.0 mm
    วันที่ 31-39  h-misalignment 1.5 mm
    วันที่ 40-48  h-misalignment 2.0 mm

เลือก h-misalignment เพราะเป็นคลาสที่ **recall ไต่ขึ้นตามความรุนแรงอย่าง
เป็นระบบที่สุด** (สหสัมพันธ์อันดับ +1.000 ดู `experiments/2026-10-04-anomaly-detector.md`)
จึงเป็นตัวแทนของการเสื่อมสภาพที่สมเหตุสมผลที่สุดในชุดข้อมูลนี้

**จุดที่ต่างจากของจริง**

* ของจริงเปลี่ยนต่อเนื่อง ไม่กระโดดเป็นขั้นทุก 9 วัน
* ของจริงมีช่วงทรงตัวและช่วงเร่งตัว
* ของจริงมีการซ่อมบำรุงที่ทำให้ค่ากลับลงมา

**กราฟนี้ตอบได้ว่า "ชั้นติดตามแนวโน้มจับแนวโน้มที่มีอยู่จริงได้ไหม"
ตอบไม่ได้ว่า "ระบบพยากรณ์ความเสียหายแม่นแค่ไหน"**

## หนึ่งการวัดต่อหนึ่งชั่วโมง ไม่ใช่ต่อ 10 วินาที

คาบส่งที่ออกแบบไว้คือ 10 วินาที = 8,640 ข้อความต่อวัน แต่แต่ละสภาวะมีไฟล์
เพียงราว 48 ไฟล์ **ถ้าจำลองที่คาบจริงต้องวนใช้ไฟล์เดิมซ้ำวันละ 180 รอบ**
ซึ่งทำให้กราฟหลอกตา เพราะจุดที่ติดกันจะเป็นไฟล์เดียวกันเป๊ะ

จึงใช้ **1 การวัดต่อชั่วโมง = 24 ต่อวัน** และวนไฟล์ตามลำดับความเร็วรอบ
เพื่อให้ความเร็วแกว่งอย่างสมจริง **จำนวนการเตือนรายวันจึงเป็นจำนวนจาก 24
ไม่ใช่จาก 8,640** ซึ่งต้องบอกไว้บนกราฟ

รัน:
    python src/viz/make_trend_report.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Ellipse
from matplotlib.ticker import MaxNLocator

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models import detector, trend  # noqa: E402
from src.paths import processed_dir, repo_root  # noqa: E402
from src.viz import style  # noqa: E402

PER_DAY = 24                 # หนึ่งการวัดต่อชั่วโมง
MODEL = repo_root() / "models" / "baseline-normal.json"
OUT = repo_root() / "reports" / "trend"

# ลำดับการเสื่อมสภาพที่ประกอบขึ้น (คลาส, กลุ่มย่อย, จำนวนวัน, ป้ายบนกราฟ)
TIMELINE = [
    ("normal", None, 12, "healthy"),
    ("horizontal-misalignment", "0.5mm", 9, "0.5 mm"),
    ("horizontal-misalignment", "1.0mm", 9, "1.0 mm"),
    ("horizontal-misalignment", "1.5mm", 9, "1.5 mm"),
    ("horizontal-misalignment", "2.0mm", 9, "2.0 mm"),
]


def build_series(grid: pd.DataFrame, model: detector.Baseline,
                 phases: list[tuple], feats: list[str]) -> pd.DataFrame:
    """ประกอบเส้นเวลาแล้วให้คะแนนทุกการวัด

    วนไฟล์ของสภาวะนั้นตามลำดับความเร็วรอบ เพื่อให้ความเร็วแกว่งสมจริง
    และ**กรองเฉพาะไฟล์ที่อยู่ในช่วงความเร็วที่เส้นฐานครอบคลุม**
    มิฉะนั้นจะได้ `indeterminate` ปนมาซึ่งไม่ใช่สิ่งที่กราฟนี้ต้องการแสดง
    """
    rows = []
    hour = 0
    for cls, sub, days, label in phases:
        m = grid.cls == cls
        if sub is not None:
            m &= grid.subclass == sub
        pool = grid[m & grid.rot_hz.between(model.speed_lo, model.speed_hi)]
        pool = pool.sort_values("rot_hz").reset_index(drop=True)
        if pool.empty:
            raise SystemExit(f"ไม่มีไฟล์สำหรับ {cls}/{sub}")
        # เลื่อนจุดเริ่มของแต่ละวันด้วยจำนวนที่เป็นเฉพาะสัมพัทธ์กับขนาด pool
        #
        # ถ้าวนไฟล์ตรงๆ ด้วย i % len(pool) จำนวนไฟล์ต่อวัน (24) กับขนาด pool
        # (ราว 48) จะหารลงตัว ทำให้**ทุกวันใช้ไฟล์ชุดเดิมเป๊ะ** แล้วจำนวน
        # การเตือนรายวันออกมาเป็นลายซ้ำอย่าง 3,0,3,0,3,0 ซึ่งเป็นร่องรอย
        # ของวิธีประกอบข้อมูล ไม่ใช่พฤติกรรมของเครื่องจักร และทำให้กราฟหลอกตา
        #
        # การเลื่อน 7 ต่อวันทำให้แต่ละวันเริ่มที่ความเร็วต่างกัน
        # ซึ่งใกล้เคียงของจริงกว่า เพราะเครื่องจักรไม่ได้เริ่มที่รอบเดิมทุกวัน
        for i in range(days * PER_DAY):
            idx = (i + 7 * (i // PER_DAY)) % len(pool)
            r = pool.iloc[idx]
            res = model.score({f: float(r[f]) for f in feats}, float(r.rot_hz))
            rows.append({
                "hour": hour, "day": hour // PER_DAY + 1, "phase": label,
                "rot_hz": float(r.rot_hz), "score": res["score"],
                "n_exceed": res["n_exceed"], "anomaly": bool(res["anomaly"]),
                "worst": res["worst"],
            })
            hour += 1
    return pd.DataFrame(rows)


def panel_threshold(ax, df: pd.DataFrame, model: detector.Baseline) -> None:
    """คะแนนตามเวลา พร้อมเส้นเกณฑ์ แถบปกติ และวงบริเวณที่ผิดปกติ"""
    d = df.day.to_numpy() + (df.hour.to_numpy() % PER_DAY) / PER_DAY
    y = df.n_exceed.to_numpy().astype(float)
    ok = ~df.anomaly.to_numpy()
    thr = model.vote_min

    # แถบ "ปกติ" อยู่ข้างหลังสุด ใช้สีจางเพื่อไม่แย่งสายตา
    ax.axhspan(0, thr, color=style.status("normal"), alpha=0.07, zorder=0)

    # จุดข้อมูล แยกสีตามสถานะ และมีขอบสีพื้นกันจุดทับกันอ่านไม่ออก
    ax.scatter(d[ok], y[ok], s=9, color=style.status("normal"),
               edgecolor=style.SURFACE, linewidth=0.4, zorder=3,
               label="within baseline")
    ax.scatter(d[~ok], y[~ok], s=14, color=style.status("anomaly"),
               edgecolor=style.SURFACE, linewidth=0.4, zorder=4,
               label="anomalous")

    # EWMA จับการเลื่อนระดับที่ค่าเดี่ยวมองไม่เห็น
    ax.plot(d, trend.ewma(y), color=style.INK, linewidth=1.8, zorder=5,
            label="EWMA (lambda 0.2)")

    # เส้นเกณฑ์ — สิ่งที่อาจารย์อยากเห็น
    ax.axhline(thr, color=style.status("anomaly"), linewidth=1.6,
               linestyle="--", zorder=6)
    ax.text(0.6, thr + 1.2, f"alarm threshold = {thr} features",
            color=style.status("anomaly"), fontsize=8, fontweight="bold")

    # เส้นแบ่งช่วงและป้ายบอกความรุนแรง
    edges = df.groupby("phase", sort=False).day.min().to_numpy()
    labels = list(df.phase.unique())
    ymax = max(y.max() * 1.18, thr * 1.6)
    for x, lbl in zip(edges, labels):
        if x > 1:
            ax.axvline(x, color=style.GRID, linewidth=1.0, zorder=1)
        ax.text(x + 0.3, ymax * 0.955, lbl, fontsize=8,
                color=style.INK_SOFT, ha="left", va="top")

    # วงบริเวณที่ผิดปกติ — เฉพาะเฟสสุดท้ายซึ่งเป็นช่วงที่ชัดที่สุด
    # ขนาดต้องพอดีกับกลุ่มจุดจริง ถ้าวงใหญ่เกินจะล้นกรอบและทับป้ายช่วง
    late = df[df.phase == labels[-1]]
    if not late.empty and late.anomaly.any():
        x0, x1 = late.day.min(), late.day.max() + 1
        yl = late[late.anomaly].n_exceed
        cy = (yl.min() + yl.max()) / 2
        half_h = (yl.max() - yl.min()) / 2 + 2.0
        ax.add_patch(Ellipse(((x0 + x1) / 2, cy), width=(x1 - x0) * 1.08,
                             height=half_h * 2, fill=False,
                             edgecolor=style.status("anomaly"),
                             linewidth=1.6, zorder=7))
        ax.annotate("sustained anomaly",
                    xy=(x0, cy), xytext=(x0 - 11.5, cy - half_h - 5.0),
                    fontsize=8, color=style.status("anomaly"),
                    fontweight="bold", ha="left", va="top",
                    arrowprops=dict(arrowstyle="->", lw=1.2,
                                    color=style.status("anomaly"),
                                    connectionstyle="arc3,rad=-0.15"))
        ymax = max(ymax, cy + half_h + 3.0)

    ax.set_xlim(0.5, df.day.max() + 2.5)
    ax.set_ylim(0, ymax)
    ax.set_xlabel("day")
    ax.set_ylabel("features outside baseline (of 72)")
    ax.set_title("A — health score over time, one measurement per hour",
                 loc="left")
    ax.legend(loc="upper left", ncol=3, bbox_to_anchor=(0, -0.14))


def panel_daily(ax, counts: list[int], days: list[int], color: str,
                title: str, note: str) -> trend.TrendResult:
    """จำนวนการเตือนรายวันเป็นแท่ง พร้อมผลการทดสอบแนวโน้ม"""
    r = trend.mann_kendall(counts)
    # แท่งกว้าง 0.78 เพื่อให้มีช่องว่างสีพื้นระหว่างแท่ง อ่านง่ายกว่าแท่งชิดกัน
    ax.bar(days, counts, width=0.78, color=color, linewidth=0, zorder=3)

    # เส้น Sen slope วางด้วยมัธยฐานทั้งสองแกน ซึ่งเป็นวิธีมาตรฐานของ Theil-Sen
    # **ต้องลากเฉพาะช่วงที่มีข้อมูลจริง** ถ้าลากเลยออกไปจะหลอกตาว่ามีข้อมูล
    # ที่ไม่เคยมี และทำให้ปลายเส้นชี้ไปยังค่าที่ไม่เคยวัดได้
    if r.verdict != "too-short" and np.isfinite(r.slope):
        x = np.asarray(days, dtype=float)
        line = float(np.median(counts)) + r.slope * (x - float(np.median(x)))
        ax.plot(x, line, color=style.INK, linewidth=1.8, linestyle="--",
                zorder=4, label=f"Sen slope {r.slope:+.2f}/day")
        ax.legend(loc="upper left")

    top = max(max(counts), 1) * 1.45
    ax.set_ylim(0, top)
    # จำนวนการเตือนเป็นจำนวนนับ แกนจึงต้องเป็นจำนวนเต็ม
    # ถ้าปล่อยให้ matplotlib เลือกเอง แผงที่ค่าน้อยจะได้ขีด 0.2 0.4 ซึ่งอ่านแล้วงง
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    # แผงที่ไม่มีการเตือนเลยจะว่างจนดูเหมือนรูปเสีย ต้องเขียนกำกับ
    if max(counts) == 0:
        ax.text(float(np.median(days)), top * 0.5, "zero alarms\non every day",
                ha="center", va="center", fontsize=9, color=style.INK_SOFT)

    verdict = {"rising": "TREND: rising", "falling": "TREND: falling",
               "no-trend": "no trend", "too-short": "too short"}[r.verdict]
    ax.set_title(f"{title}\n{verdict}  ·  tau {r.tau:+.2f}  ·  p {r.p:.4f}",
                 loc="left", pad=10)
    ax.set_xlabel(f"day   ({note})")
    ax.set_ylabel(f"anomalous hours per day (of {PER_DAY})")
    return r


def main() -> int:
    if not MODEL.is_file():
        raise SystemExit(f"ไม่พบโมเดลที่ {MODEL}\n"
                         f"สร้างก่อนด้วย: python src/models/eval_detector.py")
    style.apply()
    OUT.mkdir(parents=True, exist_ok=True)

    grid = pd.read_csv(processed_dir() / "feature_grid.csv")
    feats = [c for c in grid.columns if "." in c]
    model = detector.Baseline.load(MODEL)

    deg = build_series(grid, model, TIMELINE, feats)
    healthy = build_series(
        grid, model, [("normal", None, sum(p[2] for p in TIMELINE), "healthy")],
        feats)

    # ---------------------------------------------------- รูปที่ 1
    fig, ax = plt.subplots(figsize=(11, 4.4))
    panel_threshold(ax, deg, model)
    style.finish(
        fig,
        "Normal vs degrading — where the threshold sits",
        "Constructed timeline from MAFAULDA severity levels. "
        "NOT a measured run-to-failure.")
    fig.savefig(OUT / "01-threshold.png")
    plt.close(fig)

    # ---------------------------------------------------- รูปที่ 2
    #
    # แผง D สำคัญที่สุดสำหรับคำถามของอาจารย์
    #
    # ที่เกณฑ์จริง เครื่องปกติไม่เตือนเลยสักครั้ง (แผง C) ซึ่งเป็นข่าวดี
    # **แต่ไม่ได้แสดงประเด็นที่อาจารย์ถาม** ว่าการเตือนผิดยอมรับได้ถ้าไม่มีทิศทาง
    #
    # และที่หน้างานจริงอัตราการเตือนผิดจะไม่เป็นศูนย์ เพราะขอบบน 95%
    # ที่วัดได้คือ 0.062 ต่อข้อความ ซึ่งที่ 24 การวัดต่อวันคือราว 1.5 ครั้งต่อวัน
    #
    # แผง D จึงบีบเกณฑ์ลงให้เครื่องปกติเตือนผิดบ้าง แล้วแสดงว่า
    # **Mann-Kendall ยังตอบว่าไม่มีแนวโน้มอยู่ดี** ซึ่งคือสิ่งที่ต้องพิสูจน์
    tight = detector.Baseline.load(MODEL)
    tight.vote_min = 3
    healthy_tight = build_series(
        grid, tight, [("normal", None, sum(p[2] for p in TIMELINE), "healthy")],
        feats)

    # ไม่ใช้ sharey เพราะแผง D มีค่า 0-3 ถ้าใช้แกนร่วมกับแผง B ที่ขึ้นถึง 24
    # แท่งของ D จะเตี้ยจนมองไม่เห็นว่ากระจัดกระจาย ซึ่งเป็นประเด็นทั้งหมดของแผงนั้น
    # แต่ละแผงจึงมีแกนของตัวเอง และ y-label ของทุกแผงบอก "ของ 24" กำกับไว้
    # เพื่อไม่ให้เทียบความสูงข้ามแผงผิด
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    dc = deg.groupby("day").anomaly.sum()
    hc = healthy.groupby("day").anomaly.sum()
    tc = healthy_tight.groupby("day").anomaly.sum()
    r_deg = panel_daily(axes[0], dc.tolist(), dc.index.tolist(),
                        style.status("anomaly"),
                        "B — degrading machine", "fault worsens")
    r_ok = panel_daily(axes[1], hc.tolist(), hc.index.tolist(),
                       style.status("normal"),
                       "C — healthy, real threshold", "no fault")
    r_tight = panel_daily(axes[2], tc.tolist(), tc.index.tolist(),
                          style.status("normal"),
                          "D — healthy, threshold tightened",
                          "false alarms forced")
    fig.subplots_adjust(top=0.74, wspace=0.28)
    style.finish(
        fig,
        "Does the alarm count have a direction?",
        "Mann-Kendall on daily counts. Panel D is the key case: "
        "false alarms happen, but they have no direction.")
    fig.savefig(OUT / "02-daily-trend.png")
    plt.close(fig)

    # ------------------------------------------------- สรุปบรรทัดคำสั่ง
    print(f"วาดกราฟลง {OUT.relative_to(repo_root())}")
    print()
    print(f"เกณฑ์ของโมเดล: ต้องมีตัวชี้วัดหลุดเกณฑ์ย่อย {model.vote_min} "
          f"จาก {len(model.features)} ตัว")
    print()
    for name, df in (("เครื่องที่เสื่อมสภาพ", deg), ("เครื่องที่ปกติ", healthy)):
        print(f"{name}: {len(df):,} การวัด  "
              f"ผิดปกติ {df.anomaly.sum():,} ครั้ง "
              f"({df.anomaly.mean():.1%})")
    print()
    print("จำนวนชั่วโมงที่ผิดปกติต่อวัน")
    print(f"  เสื่อมสภาพ      : {dc.tolist()}")
    print(f"  ปกติ เกณฑ์จริง  : {hc.tolist()}")
    print(f"  ปกติ เกณฑ์บีบ(D): {tc.tolist()}")
    print()
    for name, r in (("เสื่อมสภาพ          ", r_deg), ("ปกติ เกณฑ์จริง      ", r_ok),
                    ("ปกติ เกณฑ์บีบ (D)   ", r_tight)):
        print(f"  {name}  tau={r.tau:+.3f}  p={r.p:.5f}  "
              f"slope={r.slope:+.3f}/วัน  -> {r.verdict}")
    print()
    # แนวโน้มของคะแนนจับได้เร็วกว่าจำนวนการเตือนหรือไม่
    med = deg.groupby("day").n_exceed.median()
    print("เทียบความไวระหว่างสองตัวชี้วัด บนเครื่องที่เสื่อมสภาพ")
    for lbl, seq in (("จำนวนการเตือนรายวัน", dc.tolist()),
                     ("มัธยฐานคะแนนรายวัน ", med.tolist())):
        first = None
        for n in range(4, len(seq) + 1):
            if trend.mann_kendall(seq[:n]).verdict == "rising":
                first = n
                break
        print(f"  {lbl}: ตรวจพบแนวโน้มที่วันที่ "
              f"{first if first else 'ไม่พบ'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

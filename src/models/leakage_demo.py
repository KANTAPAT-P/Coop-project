"""Checkpoint 2 ขั้น 6 — เห็น data leakage ด้วยตาตัวเอง

**คำถามเดียวที่สคริปต์นี้ตอบ** ตัวเลข accuracy ที่รายงานออกมา เปลี่ยนไปแค่ไหน
เมื่อ**เปลี่ยนแค่วิธีแบ่ง train/test** โดยที่ feature โมเดล และจำนวนข้อมูลเทรน
เหมือนกันทุกประการ

**ทำไมต้องทำ** งาน vibration classification ที่รายงาน accuracy 99–100% มีอยู่
เต็มไปหมด ส่วนใหญ่แบ่ง train/test แบบสุ่มหลังจากตัดสัญญาณเป็นหน้าต่างแล้ว
หน้าต่างที่ติดกันจากไฟล์เดียวกันจึงไปโผล่ทั้งสองฝั่ง โมเดลแค่จำว่า
"ลายเซ็นของไฟล์นี้หน้าตาแบบนี้" ก็ตอบถูกหมด โดยไม่ได้เรียนรู้อะไรเกี่ยวกับ
ความเสียหายเลย พอย้ายไปเครื่องจักรจริงที่ไม่เคยเห็นก็พังทันที

**สามวิธีแบ่ง เทรนเท่ากันหมดที่ 50%**

    random-window   สุ่มหน้าต่าง ไม่สนว่ามาจากไฟล์ไหน   <- วิธีที่รั่ว
    by-file         หน้าต่างจากไฟล์เดียวกันอยู่ฝั่งเดียวกัน
    by-speed        เทรนที่ความเร็วต่ำ ทดสอบที่ความเร็วสูง (และกลับทาง)

ส่วนต่างระหว่างสองอันแรกคือขนาดของ leakage ที่เกิดจากหน้าต่างติดกัน
ส่วนต่างระหว่างอันที่สองกับสามคือความสามารถในการ**ข้ามเงื่อนไขการทำงาน**
ซึ่งเป็นสิ่งที่ระบบจริงต้องทำได้ เพราะมอเตอร์ในโรงงานไม่ได้หมุนความเร็วเดียว
ตลอดเวลาที่เราเก็บ training set

**ขอบเขตข้อมูล** ใช้ขอบเขตที่ยุติธรรมที่สุดตาม CLAUDE.md หัวข้อ 5 คือ
bearing เอาเฉพาะมวลถ่วง 0 g (ไม่งั้นโมเดลเรียนรู้ imbalance ที่ปนมาแทน)
ส่วน imbalance เอาทุกมวลรวมเป็นคลาสเดียว ได้ช่วงความเร็วที่ครบทั้ง 6 คลาส
กว้างที่สุด 13.1–61.2 Hz

รัน:
    python src/models/leakage_demo.py              # สกัด feature ใหม่ (ราว 5 นาที)
    python src/models/leakage_demo.py --cached     # ใช้ตาราง feature เดิม
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedShuffleSplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.features.screen_signatures import CHANNELS, channel_features  # noqa: E402
from src.paths import processed_dir, repo_root, sampling_rate  # noqa: E402
from src.viz import style  # noqa: E402

FS = sampling_rate()

# หน้าต่าง 0.64 วินาที ให้ความละเอียดความถี่ 1.5625 Hz ซึ่งยังแยก 1x กับ 2x
# ได้แม้ที่ความเร็วต่ำสุด 13.1 Hz (สองพีคห่างกัน 13.1 Hz = 8 ช่องความถี่)
WIN = 32768
N_WIN = 7                       # 7 x 32768 = 229,376 แถว จาก 250,000
PEAK_TOL_HZ = 2.5 * FS / WIN    # +-2.5 ช่องความถี่ = +-3.9 Hz

HZ_RANGE = (13.1, 61.2)
SPEED_CUT = 30.0                # เส้นแบ่งของการแบ่งตามความเร็ว
PER_CLASS = 20                  # ไฟล์ต่อคลาส ครึ่งหนึ่งแต่ละฝั่งของ SPEED_CUT
N_REPEAT = 5                    # จำนวนครั้งที่สุ่มซ้ำสำหรับสองวิธีแรก
TEST_SIZE = 0.5

CLASSES = mf.CLASS_ORDER


def pick_files(index: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """เลือกไฟล์ให้ทุกคลาสมีข้อมูลทั้งสองฝั่งของเส้นแบ่งความเร็ว

    ถ้าสุ่มดื้อๆ บางคลาสอาจไปกระจุกอยู่ฝั่งเดียว แล้วการแบ่งตามความเร็ว
    จะกลายเป็นการทดสอบคลาสที่ไม่เคยเห็นเลย ซึ่งเป็นคนละโจทย์
    """
    bearing = index["cls"].isin(["underhang", "overhang"])
    sel = index[~bearing | (index["mass_g"] == 0)]      # ห้ามใช้ mass_g == 0 เดี่ยวๆ
    sel = sel[sel["rot_hz"].between(*HZ_RANGE)]

    half = PER_CLASS // 2
    rows = []
    for cls in CLASSES:
        s = sel[sel["cls"] == cls]
        for side, part in (("low", s[s["rot_hz"] < SPEED_CUT]),
                           ("high", s[s["rot_hz"] >= SPEED_CUT])):
            if part.empty:
                raise ValueError(f"คลาส {cls} ไม่มีไฟล์ฝั่ง {side} ของ {SPEED_CUT} Hz")
            rows.append(part.sample(n=min(half, len(part)), random_state=seed))
    return pd.concat(rows, ignore_index=True)


def build_table(index: pd.DataFrame) -> pd.DataFrame:
    files = pick_files(index)
    print(f"สกัด feature จาก {len(files)} ไฟล์ x {N_WIN} หน้าต่าง "
          f"= {len(files) * N_WIN} แถว")
    out = []
    for i, (_, r) in enumerate(files.iterrows(), start=1):
        rot = float(mf.speed_hz(r.to_frame().T).iloc[0])
        d = mf.load(r["path"], CHANNELS)
        for w in range(N_WIN):
            seg = d.iloc[w * WIN:(w + 1) * WIN]
            row = {"cls": r["cls"], "rel": r["rel"], "rot_hz": rot, "window": w}
            for ch in CHANNELS:
                feats = channel_features(seg[ch].to_numpy(), rot, tol_hz=PEAK_TOL_HZ)
                for k, v in feats.items():
                    row[f"{ch}.{k}"] = v
            out.append(row)
        if i % 10 == 0:
            print(f"  {i}/{len(files)}", flush=True)
    return pd.DataFrame(out)


def fit_score(tab: pd.DataFrame, feats: list[str],
              tr: np.ndarray, te: np.ndarray) -> dict:
    X = tab[feats].to_numpy()
    y = tab["cls"].to_numpy()
    clf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)
    clf.fit(X[tr], y[tr])
    pred = clf.predict(X[te])
    return {
        "acc": accuracy_score(y[te], pred),
        "f1": f1_score(y[te], pred, average="macro", labels=CLASSES, zero_division=0),
        "recall": recall_score(y[te], pred, average=None, labels=CLASSES,
                               zero_division=0),
        "cm": confusion_matrix(y[te], pred, labels=CLASSES),
        "n_train": len(tr),
    }


def run_splits(tab: pd.DataFrame) -> dict[str, dict]:
    feats = [c for c in tab.columns if "." in c]
    tab = tab.dropna(subset=feats).reset_index(drop=True)
    y, groups = tab["cls"].to_numpy(), tab["rel"].to_numpy()
    idx = np.arange(len(tab))
    results: dict[str, dict] = {}

    def summarise(name: str, runs: list[dict]) -> None:
        results[name] = {
            "acc": float(np.mean([r["acc"] for r in runs])),
            "acc_sd": float(np.std([r["acc"] for r in runs])),
            "f1": float(np.mean([r["f1"] for r in runs])),
            "recall": np.mean([r["recall"] for r in runs], axis=0),
            "cm": np.sum([r["cm"] for r in runs], axis=0),
            "n_train": int(np.mean([r["n_train"] for r in runs])),
            "n_runs": len(runs),
        }
        print(f"{name:22s} acc {results[name]['acc']:.3f} "
              f"(sd {results[name]['acc_sd']:.3f})  "
              f"macro-F1 {results[name]['f1']:.3f}", flush=True)

    # 1. สุ่มหน้าต่าง — หน้าต่างจากไฟล์เดียวกันไปได้ทั้งสองฝั่ง
    sss = StratifiedShuffleSplit(n_splits=N_REPEAT, test_size=TEST_SIZE, random_state=0)
    summarise("random-window", [fit_score(tab, feats, tr, te)
                                for tr, te in sss.split(idx, y)])

    # 2. แบ่งตามไฟล์ — ปิดช่องทางหน้าต่างติดกัน แต่ยังอยู่รอบบันทึกเดียวกัน
    gss = GroupShuffleSplit(n_splits=N_REPEAT, test_size=TEST_SIZE, random_state=0)
    summarise("by-file", [fit_score(tab, feats, tr, te)
                          for tr, te in gss.split(idx, y, groups)])

    # 3. แบ่งตามความเร็ว — เงื่อนไขการทำงานที่ไม่เคยเห็นตอนเทรน
    low = idx[tab["rot_hz"].to_numpy() < SPEED_CUT]
    high = idx[tab["rot_hz"].to_numpy() >= SPEED_CUT]
    summarise("by-speed low-to-high", [fit_score(tab, feats, low, high)])
    summarise("by-speed high-to-low", [fit_score(tab, feats, high, low)])
    return results


ORDER = ["random-window", "by-file", "by-speed low-to-high", "by-speed high-to-low"]
BAR_COLORS = ["#c2352b", style.CLASS_COLORS["normal"],
              style.CLASS_COLORS["overhang"], style.CLASS_COLORS["vertical-misalignment"]]
SHORT = {"normal": "normal", "imbalance": "imbal", "horizontal-misalignment": "h-mis",
         "vertical-misalignment": "v-mis", "underhang": "under", "overhang": "over"}


def make_figure(res: dict[str, dict], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6),
                             gridspec_kw={"width_ratios": [1, 1.5]})
    chance = 1.0 / len(CLASSES)

    ax = axes[0]
    bars = ax.bar(range(len(ORDER)), [res[k]["acc"] for k in ORDER], color=BAR_COLORS)
    for i, (b, k) in enumerate(zip(bars, ORDER)):
        ax.text(i, b.get_height() + 0.02, f"{res[k]['acc']:.3f}",
                ha="center", fontsize=9, color=style.INK)
    ax.axhline(chance, color=style.MARKER, linestyle=(0, (3, 3)), linewidth=0.9)
    ax.annotate("chance (1/6)", xy=(len(ORDER) - 0.5, chance), xytext=(0, 3),
                textcoords="offset points", ha="right", fontsize=7.5, color=style.MARKER)
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels([k.replace(" ", "\n") for k in ORDER], fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Test accuracy")
    ax.set_title("Same features, same model, same training size", fontsize=10, loc="left")

    ax = axes[1]
    w = 0.2
    for j, k in enumerate(ORDER):
        ax.bar(np.arange(len(CLASSES)) + (j - 1.5) * w, res[k]["recall"], width=w,
               label=k, color=BAR_COLORS[j])
    ax.set_xticks(range(len(CLASSES)))
    ax.set_xticklabels([SHORT[c] for c in CLASSES], fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Recall")
    ax.legend(ncol=2, loc="upper right", fontsize=7.5)
    ax.set_title("Per-class recall — which classes survive an honest split",
                 fontsize=10, loc="left")

    style.finish(fig, "Data leakage: the split decides the score",
                 f"MAFAULDA - 6 classes - bearing 0 g - {HZ_RANGE[0]}-{HZ_RANGE[1]} Hz - "
                 f"{WIN / FS * 1000:.0f} ms windows - random forest - "
                 "train = 50% of the windows in every split")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path)
    plt.close(fig)


def report(tab: pd.DataFrame, res: dict[str, dict], fig_rel: str) -> str:
    n_files = tab["rel"].nunique()
    n_feat = len([c for c in tab.columns if "." in c])
    lines = [
        "# วิธีแบ่ง train/test เปลี่ยนคะแนนไปแค่ไหน (Checkpoint 2 ขั้น 6)",
        "",
        f"- วันที่: {date.today().isoformat()}",
        "- สคริปต์: `src/models/leakage_demo.py`",
        f"- ข้อมูล: {n_files} ไฟล์ · {len(tab)} หน้าต่าง · "
        f"หน้าต่างละ {WIN} แถว ({WIN / FS * 1000:.0f} ms) · {N_WIN} หน้าต่างต่อไฟล์",
        "- ขอบเขต: 6 คลาส · bearing มวล 0 g · imbalance ทุกมวล · "
        f"ความเร็ว {HZ_RANGE[0]}–{HZ_RANGE[1]} Hz",
        f"- feature: {n_feat} ตัว (11 ตัว × {len(CHANNELS)} ช่อง ไม่รวม mic)",
        "- โมเดล: random forest 300 ต้น ค่าอื่นเป็นค่าเริ่มต้น",
        f"- **ทุกวิธีเทรนด้วยข้อมูล 50% เท่ากัน** สองวิธีแรกสุ่มซ้ำ {N_REPEAT} ครั้ง",
        "",
        "## ผล",
        "",
        "| วิธีแบ่ง | accuracy | sd | macro-F1 | หน้าต่างที่ใช้เทรน |",
        "|---|---:|---:|---:|---:|",
    ]
    for k in ORDER:
        r = res[k]
        sd = f"{r['acc_sd']:.3f}" if r["n_runs"] > 1 else "—"
        lines.append(f"| `{k}` | **{r['acc']:.3f}** | {sd} | {r['f1']:.3f} | {r['n_train']} |")
    lines += [
        "",
        f"เดาสุ่มได้ {1 / len(CLASSES):.3f}",
        "",
        f"![ผลการแบ่งสามแบบ]({fig_rel})",
        "",
        "## recall รายคลาส",
        "",
        "| คลาส | " + " | ".join(f"`{k}`" for k in ORDER) + " |",
        "|---|" + "---:|" * len(ORDER),
    ]
    for i, c in enumerate(CLASSES):
        lines.append(f"| {c} | "
                     + " | ".join(f"{res[k]['recall'][i]:.2f}" for k in ORDER) + " |")

    lines += ["", "## confusion matrix ของ `by-speed low-to-high`", "",
              "แถว = ของจริง คอลัมน์ = ที่ทาย", "",
              "| จริง \\ ทาย | " + " | ".join(SHORT[c] for c in CLASSES) + " |",
              "|---|" + "---:|" * len(CLASSES)]
    cm = res["by-speed low-to-high"]["cm"]
    for i, c in enumerate(CLASSES):
        lines.append(f"| {SHORT[c]} | " + " | ".join(str(int(v)) for v in cm[i]) + " |")

    rw, bf = res["random-window"]["acc"], res["by-file"]["acc"]
    lo, hi = res["by-speed low-to-high"]["acc"], res["by-speed high-to-low"]["acc"]
    lines += [
        "",
        "## อ่านผลยังไง",
        "",
        f"**1. การสุ่มหน้าต่างเติมคะแนนให้ฟรี {(rw - bf) * 100:.0f} จุด** "
        f"({rw:.3f} เทียบกับ {bf:.3f}) ไม่ได้แปลว่าโมเดลเก่งขึ้น แต่แปลว่าชุดทดสอบ"
        f"มีหน้าต่างพี่น้องจากไฟล์เดียวกันกับที่เทรนไปแล้ว หน้าต่างสองอันที่ห่างกัน "
        f"{WIN / FS:.2f} วินาทีในไฟล์เดียวกันมาจากเครื่องตัวเดียวกัน ความเร็วเดียวกัน "
        "การประกอบเดียวกัน โมเดลแค่จำไฟล์ได้ก็ตอบถูก",
        "",
        f"**2. แม้แบ่งตามไฟล์แล้วก็ยังพองอยู่อีกชั้น** พอบังคับให้ทดสอบที่ความเร็วที่"
        f"ไม่เคยเห็น คะแนนตกจาก {bf:.3f} เหลือ {lo:.3f} ส่วนต่างก้อนนี้คือส่วนที่"
        "โมเดลอาศัยความเร็วรอบ ไม่ใช่ความเสียหาย ซึ่งเป็น leakage คนละช่องทาง"
        "กับหน้าต่างติดกัน และเป็นช่องทางที่ระบบจริงเจอแน่นอน",
        "",
        f"**3. สองทิศไม่เท่ากัน** เทรนความเร็วต่ำแล้วทดสอบสูงได้ {lo:.3f} "
        f"แต่เทรนความเร็วสูงแล้วทดสอบต่ำได้ {hi:.3f} "
        "ที่ความเร็วสูงความเสียหายถูกกระตุ้นแรงกว่า ตัวอย่างที่เทรนจึงมีสัญญาณชัดกว่า "
        "**ถ้าเก็บ training set ได้ช่วงเดียว ให้เลือกเก็บตอนเครื่องทำงานหนัก**",
        "",
        "**4. คลาสที่รอดทุกวิธีคือ imbalance** ตรงกับที่คัดกรองลายเซ็นไว้ว่า"
        "สัดส่วนพลังงานที่ 1× เพิ่มตามมวลอย่างเป็นระบบ ส่วน bearing สองฝั่งตกหนักที่สุด"
        "และไปสับสนกับ misalignment ดูใน confusion matrix ข้างบน",
        "",
        "## ข้อจำกัดที่ยังเหลือ",
        "",
        "การแบ่งตามไฟล์ **ยังไม่ใช่การแบ่งที่ซื่อสัตย์ที่สุด** เพราะไฟล์ทุกไฟล์ในกลุ่มย่อย"
        "เดียวกันน่าจะบันทึกรวดเดียวในการติดตั้งครั้งเดียว การแบ่งที่ซื่อสัตย์จริงต้องแบ่ง"
        "ข้าม**รอบบันทึก** หรือข้ามเครื่องจักร ซึ่ง MAFAULDA ไม่ได้บันทึกไว้ว่าไฟล์ไหน"
        f"มาจากการประกอบครั้งไหน ดังนั้นตัวเลข {bf:.3f} เองก็ยังเป็นค่าที่สูงเกินจริง",
        "",
        "**สิ่งที่ต้องรายงานคู่กับ accuracy เสมอคือวิธีแบ่ง train/test** "
        "ตัวเลขเดียวกันบนข้อมูลชุดเดียวกันต่างกันได้ "
        f"{(rw - lo) * 100:.0f} จุด แค่เปลี่ยนวิธีแบ่ง",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="สาธิต data leakage จากวิธีแบ่ง train/test")
    ap.add_argument("--cached", action="store_true", help="ใช้ตาราง feature ที่สกัดไว้แล้ว")
    args = ap.parse_args()

    style.apply()
    cache = processed_dir() / "leakage_windows.csv"
    if args.cached and cache.is_file():
        tab = pd.read_csv(cache)
    else:
        tab = build_table(mf.build_index())
        cache.parent.mkdir(parents=True, exist_ok=True)
        tab.to_csv(cache, index=False)

    res = run_splits(tab)

    fig_path = repo_root() / "reports" / "eda" / "08-split-leakage.png"
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    make_figure(res, fig_path)

    text = report(tab, res, f"../reports/eda/{fig_path.name}")
    out = repo_root() / "experiments" / f"{date.today().isoformat()}-split-leakage.md"
    out.write_text(text + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานลง {out.relative_to(repo_root())}")
    print(f"กราฟ {fig_path.relative_to(repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

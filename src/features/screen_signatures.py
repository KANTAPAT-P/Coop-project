"""คัดกรองหา "ลายเซ็น" ของความผิดปกติแต่ละชนิด แบบเป็นระบบ

**คำถาม** feature ตัวไหน บนช่องไหน ที่แยกความผิดปกติชนิดหนึ่งออกจาก**ทุกชนิดอื่น**ได้

**ทำไมต้องเทียบกับทุกกลุ่ม ไม่ใช่แค่ normal** เคยสรุปว่า envelope floor แยก
bearing fault ได้ เพราะทดสอบกับ normal และไม่กี่กลุ่ม พอใส่ misalignment เข้ามา
ข้อสรุปพังทันที ลายเซ็นที่ใช้ได้จริงต้อง**เจาะจง** คือแยกออกจากทุกกลุ่มที่มี

**ตัววัด** AUC แบบ one-vs-rest ของ feature ทีละตัว
    1.0 หรือ 0.0 = แยกขาดทุกไฟล์ (0.0 คือค่าต่ำกว่ากลุ่มอื่นทุกไฟล์)
    0.5         = แยกไม่ได้เลย เหมือนเดาสุ่ม
รายงานเป็น "ความแรงของการแยก" = |AUC - 0.5| x 2 อยู่ในช่วง 0 ถึง 1

**สอง feature family**
    amplitude   ขึ้นกับความแรงของสัญญาณ (rms, p2p, envelope floor)
                ถ้าความไวของเซ็นเซอร์เปลี่ยนระหว่างรอบบันทึก ค่าพวกนี้เพี้ยนตาม
    robust      ไม่ขึ้นกับความไวของเซ็นเซอร์ (อัตราส่วน, สัดส่วนพลังงาน, kurtosis, crest)
                เชื่อถือได้กว่า เพราะเรายังสงสัยเรื่องการติดตั้งเซ็นเซอร์ต่างกันในแต่ละคลาส

**ทุก feature คำนวณหลังกรองความถี่ต่ำกว่า 10 Hz ทิ้ง** เพื่อตัด drift ของเซ็นเซอร์
ที่พบในช่อง o_axial (ความเร็วรอบต่ำสุดในช่วงที่ใช้คือ 20 Hz จึงไม่เสียส่วน 1x)

รัน:
    python src/features/screen_signatures.py              # คำนวณ feature ใหม่ (ราว 5 นาที)
    python src/features/screen_signatures.py --cached     # ใช้ตาราง feature เดิม
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import butter, sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.data.check_speed_coverage import md_table  # noqa: E402
from src.features import spectral  # noqa: E402
from src.paths import processed_dir, repo_root, sampling_rate  # noqa: E402

FS = sampling_rate()
CHANNELS = ["u_axial", "u_radial", "u_tang", "o_axial", "o_radial", "o_tang"]
HZ_RANGE = (20.0, 42.0)
PER_GROUP = 25

# (ชื่อกลุ่ม, cls, subclass, mass_g ที่ยอมรับ)
GROUPS = [
    ("normal", "normal", None, None),
    ("imbalance light 6-15g", "imbalance", None, (6, 10, 15)),
    ("imbalance heavy 25-35g", "imbalance", None, (25, 30, 35)),
    ("h-misalign", "horizontal-misalignment", None, None),
    ("v-misalign", "vertical-misalignment", None, None),
    ("under outer", "underhang", "outer_race", (0,)),
    ("under ball", "underhang", "ball_fault", (0,)),
    ("under cage", "underhang", "cage_fault", (0,)),
    ("over outer", "overhang", "outer_race", (0,)),
    ("over ball", "overhang", "ball_fault", (0,)),
    ("over cage", "overhang", "cage_fault", (0,)),
]

# feature ชื่อไหนอยู่ family ไหน
ROBUST = {"kurt", "crest", "h1_frac", "r21", "kurt_band", "e_low", "e_mid", "e_high", "env_rel"}
AMPLITUDE = {"rms", "env_floor"}

_HP = butter(4, 10.0, btype="highpass", fs=FS, output="sos")


def channel_features(x: np.ndarray, rot: float) -> dict[str, float]:
    """feature ทั้งหมดของหนึ่งช่อง ทุกตัวคำนวณบนไมโครคอนโทรลเลอร์ได้"""
    x = sosfiltfilt(_HP, x - x.mean())
    rms = float(np.sqrt(np.mean(x ** 2)))
    f, m = spectral.spectrum(x, FS)
    power = m ** 2
    total = float(power[(f > 5) & (f < 10000)].sum())

    a1 = spectral.peak_near(f, m, rot, tol_frac=0.02)[1]
    a2 = spectral.peak_near(f, m, 2 * rot, tol_frac=0.02)[1]

    def frac(lo, hi):
        return float(power[(f >= lo) & (f < hi)].sum()) / total

    band = spectral.bandpass(x, FS, *spectral.DEFAULT_BAND)
    fe, me = spectral.envelope_spectrum(x, FS)
    env_floor = float(np.median(me[(fe > 2) & (fe <= 250)]))
    band_rms = float(np.sqrt(np.mean(band ** 2)))

    return {
        "rms": rms,
        "kurt": float(stats.kurtosis(x, fisher=False)),
        "crest": float(np.max(np.abs(x)) / rms),
        # พลังงานที่ 1x เป็นสัดส่วนของพลังงานรวม (a/sqrt2 คือ rms ของไซน์)
        "h1_frac": float((a1 / np.sqrt(2)) ** 2 / rms ** 2),
        "r21": float(a2 / a1) if a1 > 0 else np.nan,
        # รูปร่างสเปกตรัม: สัดส่วนพลังงานในสามย่าน
        "e_low": frac(5, 10 * rot),          # ถึง 10x ของความเร็วรอบ
        "e_mid": frac(10 * rot, 2000),
        "e_high": frac(2000, 10000),
        "kurt_band": float(stats.kurtosis(band, fisher=False)),
        "env_floor": env_floor,
        # envelope floor หารด้วยความแรงของย่านเดียวกัน ไม่ขึ้นกับความไวเซ็นเซอร์
        "env_rel": env_floor / band_rms if band_rms > 0 else np.nan,
    }


def pick_files(index: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, cls, sub, masses in GROUPS:
        s = index[index["cls"] == cls]
        if sub is not None:
            s = s[s["subclass"] == sub]
        if masses is not None:
            s = s[s["mass_g"].isin(masses)]
        s = s[s["rot_hz"].between(*HZ_RANGE)]
        s = s.sample(n=min(PER_GROUP, len(s)), random_state=0)
        rows.append(s.assign(group=name))
    return pd.concat(rows, ignore_index=True)


def build_table(index: pd.DataFrame) -> pd.DataFrame:
    files = pick_files(index)
    print(f"คำนวณ feature จาก {len(files)} ไฟล์ ช่วงความเร็ว {HZ_RANGE[0]:.0f}-{HZ_RANGE[1]:.0f} Hz")
    out = []
    for i, (_, r) in enumerate(files.iterrows(), start=1):
        rot = float(mf.speed_hz(r.to_frame().T).iloc[0])
        d = mf.load(r["path"], CHANNELS)
        row = {"group": r["group"], "rel": r["rel"], "rot_hz": rot}
        for ch in CHANNELS:
            for k, v in channel_features(d[ch].to_numpy(), rot).items():
                row[f"{ch}.{k}"] = v
        out.append(row)
        if i % 25 == 0:
            print(f"  {i}/{len(files)}", flush=True)
    return pd.DataFrame(out)


def auc_one_vs_rest(tab: pd.DataFrame) -> pd.DataFrame:
    """AUC ของทุก feature ในการแยกแต่ละกลุ่มออกจากกลุ่มอื่นทั้งหมด"""
    feats = [c for c in tab.columns if "." in c]
    rows = []
    for g in tab["group"].unique():
        pos = tab["group"] == g
        for f in feats:
            a, b = tab.loc[pos, f].dropna(), tab.loc[~pos, f].dropna()
            if len(a) < 5 or len(b) < 5:
                continue
            u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
            auc = u / (len(a) * len(b))
            ch, name = f.split(".")
            rows.append({"group": g, "feature": f, "channel": ch, "name": name,
                         "family": "robust" if name in ROBUST else "amplitude",
                         "auc": auc, "strength": abs(auc - 0.5) * 2,
                         "direction": "สูงกว่า" if auc > 0.5 else "ต่ำกว่า",
                         "median_in": float(a.median()), "median_rest": float(b.median())})
    return pd.DataFrame(rows)


def report(tab: pd.DataFrame, res: pd.DataFrame) -> str:
    lines = [
        "# คัดกรองลายเซ็นของความผิดปกติแต่ละชนิด",
        "",
        f"- วันที่: {date.today().isoformat()}",
        "- สคริปต์: `src/features/screen_signatures.py`",
        f"- ไฟล์: {len(tab)} ไฟล์ · ความเร็ว {HZ_RANGE[0]:.0f}–{HZ_RANGE[1]:.0f} Hz · "
        f"สุ่มกลุ่มละไม่เกิน {PER_GROUP} ไฟล์ · bearing ใช้มวล 0 g",
        f"- feature: {res['feature'].nunique()} ตัว ({len(CHANNELS)} ช่อง)",
        "- ตัววัด: AUC แบบ one-vs-rest · ความแรง = |AUC−0.5|×2 (1 = แยกขาด, 0 = แยกไม่ได้)",
        "",
        "## จำนวนไฟล์ต่อกลุ่ม",
        "",
        md_table(tab.groupby("group").size().rename("ไฟล์").to_frame(), "กลุ่ม"),
        "",
        "## feature ที่ดีที่สุดของแต่ละกลุ่ม",
        "",
        "แยกสองคอลัมน์: ตัวที่ดีที่สุดโดยรวม และตัวที่ดีที่สุดใน family ที่**ไม่ขึ้นกับความไวเซ็นเซอร์**",
        "",
        "| กลุ่ม | ดีสุดโดยรวม | ความแรง | ดีสุดแบบ robust | ความแรง |",
        "|---|---|---:|---|---:|",
    ]
    for g in [x[0] for x in GROUPS]:
        sub = res[res["group"] == g].sort_values("strength", ascending=False)
        if sub.empty:
            continue
        b = sub.iloc[0]
        rb = sub[sub["family"] == "robust"].iloc[0]
        lines.append(
            f"| {g} | `{b.feature}` {b.direction} | {b.strength:.2f} | "
            f"`{rb.feature}` {rb.direction} | {rb.strength:.2f} |"
        )
    lines.append("")

    lines += ["## รายละเอียด 5 อันดับแรกของแต่ละกลุ่ม", ""]
    for g in [x[0] for x in GROUPS]:
        sub = res[res["group"] == g].sort_values("strength", ascending=False).head(5)
        if sub.empty:
            continue
        lines += [f"### {g}", "",
                  "| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |",
                  "|---|---|---:|---|---:|---:|"]
        for _, r in sub.iterrows():
            lines.append(f"| `{r.feature}` | {r.family} | {r.strength:.2f} | {r.direction} | "
                         f"{r.median_in:.4g} | {r.median_rest:.4g} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="คัดกรองลายเซ็นของความผิดปกติ")
    ap.add_argument("--cached", action="store_true", help="ใช้ตาราง feature ที่คำนวณไว้แล้ว")
    args = ap.parse_args()

    cache = processed_dir() / "signature_features.csv"
    if args.cached and cache.is_file():
        tab = pd.read_csv(cache)
    else:
        tab = build_table(mf.build_index())
        cache.parent.mkdir(parents=True, exist_ok=True)
        tab.to_csv(cache, index=False)

    res = auc_one_vs_rest(tab)
    res.to_csv(processed_dir() / "signature_auc.csv", index=False)

    text = report(tab, res)
    out = repo_root() / "experiments" / f"{date.today().isoformat()}-signature-screen.md"
    out.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nเขียนรายงานลง {out.relative_to(repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

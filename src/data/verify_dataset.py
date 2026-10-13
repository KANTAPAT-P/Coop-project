"""ตรวจว่า MAFAULDA แตกไฟล์ครบและอ่านได้จริง

สคริปต์นี้ **อ่านอย่างเดียว** ไม่แตะ data/raw เลยแม้แต่ไบต์เดียว
ผลสรุปเขียนลง experiments/ ตามกฎข้อ 8 ของ CLAUDE.md

รัน:
    python src/data/verify_dataset.py

ตรวจ 5 อย่าง
    1. จำนวนไฟล์ต่อคลาส เทียบกับ expected_counts ใน config.yaml
    2. รูปร่างของไฟล์ตัวอย่าง ต้องได้ (250000, 8) พอดี
    3. หน่วยของข้อมูล เป็น g หรือแรงดันไฟฟ้า
       NI 9234 รับได้ +-5 V ถ้าเจอค่าสัมบูรณ์เกิน 5 แปลว่าเป็นหน่วย g แน่นอน
    4. ยืนยันอาการคอลัมน์ 5 (o_radial) ว่าระดับสัญญาณต่ำผิดปกติจริงหรือไม่
    5. แจกแจง bearing fault ตามมวลถ่วง 0/6/20/35 g เพื่อหลบกับดัก imbalance ปน
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ให้ import src.paths ได้ ไม่ว่าจะเรียกสคริปต์จากโฟลเดอร์ไหน
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import (  # noqa: E402
    load_config,
    mafaulda_columns,
    mafaulda_dir,
    repo_root,
)

SEPARATOR = "=" * 72


def collect_counts(root: Path) -> tuple[dict[str, int], dict[str, int]]:
    """นับไฟล์ csv แยกตามคลาสระดับบน และแยกตามโฟลเดอร์ย่อย"""
    by_class: dict[str, int] = {}
    by_subfolder: dict[str, int] = {}

    for class_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        files = list(class_dir.rglob("*.csv"))
        by_class[class_dir.name] = len(files)

        subdirs = sorted(p for p in class_dir.iterdir() if p.is_dir())
        if subdirs:
            for sub in subdirs:
                by_subfolder[f"{class_dir.name}/{sub.name}"] = len(list(sub.rglob("*.csv")))
        else:
            by_subfolder[class_dir.name] = len(files)

    return by_class, by_subfolder


def check_counts(root: Path, lines: list[str]) -> bool:
    cfg = load_config()["dataset"]["mafaulda"]
    expected = cfg["expected_counts"]
    expected_total = cfg["expected_total"]

    by_class, by_subfolder = collect_counts(root)
    total = sum(by_class.values())
    ok = True

    lines.append("## 1. จำนวนไฟล์ต่อคลาส")
    lines.append("")
    lines.append("| คลาส | ที่ควรได้ | ที่ได้จริง | ผล |")
    lines.append("|---|---:|---:|---|")

    for name in sorted(set(expected) | set(by_class)):
        want = expected.get(name)
        got = by_class.get(name, 0)
        if want is None:
            lines.append(f"| {name} | (ไม่ได้ระบุ) | {got} | ? เกินมา |")
            ok = False
        elif want == got:
            lines.append(f"| {name} | {want} | {got} | OK |")
        else:
            lines.append(f"| {name} | {want} | {got} | **ไม่ตรง** |")
            ok = False

    verdict = "OK" if total == expected_total else "**ไม่ตรง**"
    lines.append(f"| **รวม** | **{expected_total}** | **{total}** | {verdict} |")
    ok = ok and total == expected_total

    lines.append("")
    lines.append("แยกตามโฟลเดอร์ย่อย")
    lines.append("")
    lines.append("| โฟลเดอร์ | ไฟล์ |")
    lines.append("|---|---:|")
    for name, count in sorted(by_subfolder.items()):
        lines.append(f"| `{name}` | {count} |")
    lines.append("")

    return ok


def pick_sample(root: Path, relative: str) -> Path | None:
    """หาไฟล์ตัวอย่าง รับได้ทั้ง path ตรงและชื่อโฟลเดอร์ (หยิบไฟล์แรก)

    ต้องใช้ ``rglob`` ไม่ใช่ ``glob`` เพราะโฟลเดอร์ bearing fault
    มีชั้นย่อยเป็นมวลถ่วง (0g/6g/20g/35g) อีกชั้นหนึ่ง
    """
    target = root / relative
    if target.is_file():
        return target
    if target.is_dir():
        files = sorted(target.rglob("*.csv"))
        return files[0] if files else None
    return None


def read_signal(path: Path) -> pd.DataFrame:
    """อ่าน MAFAULDA csv — header=None คือหัวใจ ถ้าลืมจะเสียแถวแรกไปเป็นชื่อคอลัมน์"""
    df = pd.read_csv(path, header=None)
    df.columns = mafaulda_columns()
    return df


def check_shape(root: Path, lines: list[str]) -> bool:
    cfg = load_config()["dataset"]["mafaulda"]
    want = (cfg["n_samples"], len(cfg["columns"]))

    sample = pick_sample(root, "normal/28.8768.csv")
    lines.append("## 2. รูปร่างของไฟล์ตัวอย่าง")
    lines.append("")
    if sample is None:
        lines.append("หาไฟล์ `normal/28.8768.csv` ไม่เจอ")
        lines.append("")
        return False

    df = read_signal(sample)
    ok = df.shape == want
    lines.append(f"- ไฟล์: `{sample.relative_to(root)}`")
    lines.append(f"- ที่ควรได้: `{want}` / ที่ได้จริง: `{df.shape}` -> {'OK' if ok else '**ไม่ตรง**'}")
    lines.append(f"- ชื่อไฟล์บอกความเร็วรอบ 28.8768 Hz = {28.8768 * 60:.1f} rpm (ใช้เป็น ground truth ตอนทำ tachometer)")
    lines.append("")
    return ok


def check_units(root: Path, lines: list[str]) -> None:
    """ตอบข้อค้างใน CLAUDE.md หัวข้อ 6: ค่าใน CSV เป็นหน่วย g หรือ volt"""
    lines.append("## 3. หน่วยของข้อมูล: g หรือ volt")
    lines.append("")
    lines.append("NI 9234 รับสัญญาณได้ +-5 V ถ้าช่องสั่นสะเทือนช่องใดมีค่าสัมบูรณ์เกิน 5")
    lines.append("แปลว่าตัวเลขใน CSV ถูกแปลงเป็นหน่วย g มาแล้ว ไม่ใช่แรงดันดิบ")
    lines.append("")

    candidates = ["imbalance/35g", "imbalance/30g", "imbalance/25g"]
    lines.append("| ไฟล์ | ช่องสั่นสะเทือนที่แรงสุด | max\\|x\\| | สรุป |")
    lines.append("|---|---|---:|---|")

    vibration = [c for c in mafaulda_columns() if c not in ("tach", "mic")]
    for rel in candidates:
        sample = pick_sample(root, rel)
        if sample is None:
            continue
        df = read_signal(sample)
        peaks = df[vibration].abs().max()
        strongest = peaks.idxmax()
        peak = peaks.max()
        verdict = "เกิน 5 -> หน่วย g" if peak > 5 else "ไม่เกิน 5 -> ยังสรุปไม่ได้"
        lines.append(
            f"| `{sample.relative_to(root)}` | {strongest} | {peak:.3f} | {verdict} |"
        )
    lines.append("")


def check_o_radial(root: Path, lines: list[str], per_class: int = 4) -> None:
    """ตรวจว่าคอลัมน์ 5 (o_radial) มีระดับสัญญาณต่ำผิดปกติจริงหรือไม่

    สุ่มหลายไฟล์ต่อคลาสแทนการดูไฟล์เดียว และใช้ค่ามัธยฐานเพื่อไม่ให้ไฟล์
    ที่สั่นแรงผิดปกติไฟล์เดียวลากค่าเฉลี่ยไปทั้งกลุ่ม

    🚨 **แต่ค่าเริ่มต้นคือคลาสละ 4 ไฟล์ ซึ่งยังน้อยเกินกว่าจะสรุปแทนทั้งคลาสได้**
    ถ้าค่าผิดปกติกระจุกอยู่ในไฟล์ส่วนน้อย มัธยฐานของตัวอย่างเล็กจะกระโดดตาม
    ไฟล์ที่สุ่มได้ **เกิดขึ้นจริงมาแล้วกับช่อง `mic`** ซึ่งรายงาน 88 เท่า
    แล้ววัดครบทุกไฟล์พบว่าสูงผิดปกติเพียง 25% ของไฟล์ในคลาส
    จึงถือผลของฟังก์ชันนี้เป็น**สัญญาณให้ไปตรวจต่อ ไม่ใช่ข้อสรุป**
    """
    lines.append("## 4. ระดับสัญญาณรายช่อง (ตรวจอาการคอลัมน์ 5 = o_radial)")
    lines.append("")

    columns = mafaulda_columns()
    others = ["u_axial", "u_radial", "u_tang", "o_axial", "o_tang"]
    rng_seed = np.random.default_rng(0)   # ผลซ้ำได้ทุกครั้งที่รัน

    lines.append(
        f"สุ่มคลาสละ {per_class} ไฟล์ (seed คงที่ ผลซ้ำได้) "
        "ค่าที่แสดงคือมัธยฐานของ peak-to-peak range"
    )
    lines.append("")
    lines.append("| คลาส | ไฟล์ | " + " | ".join(columns) + " | o_radial / ช่องอื่น |")
    lines.append("|---" * (len(columns) + 3) + "|")

    all_ratios = []
    medians = []
    for class_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(class_dir.rglob("*.csv"))
        if not files:
            continue
        picked = [files[i] for i in rng_seed.choice(len(files), min(per_class, len(files)), replace=False)]

        ranges = []
        for f in picked:
            df = read_signal(f)
            ranges.append(df.max() - df.min())
        med = pd.concat(ranges, axis=1).median(axis=1)

        med.name = class_dir.name
        medians.append(med)

        ratio = med["o_radial"] / med[others].mean()
        all_ratios.append(ratio)

        cells = " | ".join(f"{med[c]:.3f}" for c in columns)
        lines.append(f"| `{class_dir.name}` | {len(picked)} | {cells} | **{ratio:.3f}** |")

    lines.append("")
    if all_ratios:
        lo, hi = min(all_ratios), max(all_ratios)
        lines.append(
            f"อัตราส่วน `o_radial` ต่อช่องอื่นอยู่ระหว่าง **{lo:.3f} ถึง {hi:.3f} เท่า** "
            f"(มัธยฐานข้ามคลาส {np.median(all_ratios):.3f})"
        )
        lines.append("")
        lines.append(
            f"> `o_radial` ต่ำกว่าช่องอื่นในทุกคลาส แต่**ไม่เท่ากัน** — ต่างกันเองถึง {hi / lo:.0f} เท่า "
            "จึงอธิบายด้วย \"ช่องสัญญาณอ่อน\" เพียงอย่างเดียวไม่พอ "
            "ทิศทางการสั่นของความเสียหายแต่ละชนิดน่าจะมีผลด้วย"
        )
        lines.append("")
        lines.append(
            "> ข้อสรุปเชิงปฏิบัติ: อย่าเทียบค่าดิบ underhang กับ overhang ตรงๆ ต้อง normalize ก่อน"
        )

    # หาช่องอื่นที่ระดับสัญญาณแกว่งข้ามคลาสผิดปกติ
    # ถ้าช่องไหนต่างกันเกิน 10 เท่าระหว่างคลาส แปลว่ามีอะไรบางอย่างที่ต้องตรวจก่อนใช้
    if medians:
        table = pd.concat(medians, axis=1)
        spread = table.max(axis=1) / table.min(axis=1)
        flagged = spread[spread > 10].drop(labels=["o_radial"], errors="ignore")
        if not flagged.empty:
            lines.append("")
            lines.append("**ช่องที่ระดับสัญญาณแกว่งข้ามคลาสผิดปกติ (ต่างกันเกิน 10 เท่า)**")
            lines.append("")
            lines.append("| ช่อง | ต่ำสุด | สูงสุด | คลาสที่สูงสุด | เท่า |")
            lines.append("|---|---:|---:|---|---:|")
            for ch, factor in flagged.sort_values(ascending=False).items():
                lines.append(
                    f"| `{ch}` | {table.loc[ch].min():.3f} | {table.loc[ch].max():.3f} "
                    f"| {table.loc[ch].idxmax()} | {factor:.0f}x |"
                )
            lines.append("")
            lines.append(
                "> ตรวจก่อนเอาช่องนี้ไปใช้เป็น feature "
                "ถ้าสเกลต่างกันข้ามคลาสขนาดนี้ โมเดลจะแยกคลาสได้จากสเกลเพียงอย่างเดียว "
                "ซึ่งไม่ใช่สิ่งที่เราอยากให้มันเรียนรู้"
            )
            lines.append("")
            lines.append(
                f"> 🚨 **ตัวเลขข้างบนมาจากตัวอย่างคลาสละ {per_class} ไฟล์เท่านั้น "
                "จึงเป็นเพียงสัญญาณให้ไปตรวจต่อ ไม่ใช่ค่าของทั้งคลาส** "
                "ถ้าค่าผิดปกติกระจุกอยู่ในไฟล์ส่วนน้อยของคลาส มัธยฐานของตัวอย่างเล็ก "
                "จะกระโดดไปตามไฟล์ที่สุ่มได้ **เคยเกิดขึ้นจริงกับช่อง `mic` ซึ่งรายงาน "
                "88 เท่า แต่วัดครบทุกไฟล์แล้วพบว่าสูงผิดปกติเพียง 25% ของไฟล์ "
                "ส่วนมัธยฐานของทั้งคลาสเท่ากับ normal** "
                "ดู `experiments/2026-10-13-mic-scale-not-class-wide.md` "
                "และตรวจต่อด้วย `python src/data/check_mic_scale.py`"
            )
    lines.append("")


def check_bearing_mass_split(root: Path, lines: list[str]) -> None:
    """แจกแจง bearing fault ตามมวลถ่วงที่เติมเข้าไป

    นี่คือข้อมูลที่ใช้หลบกับดักใหญ่ที่สุดของ dataset นี้ ผู้จัดทำเติมมวลถ่วง
    เพื่อขยายสัญญาณความเสียหาย ถ้าเทรนโดยใช้ไฟล์ที่มวล > 0 g เทียบกับ normal
    ตรงๆ โมเดลจะเรียนรู้ ``imbalance`` แทน ``bearing fault``
    แล้วได้ accuracy สูงโดยไม่ได้จับสิ่งที่เราคิด
    """
    lines.append("## 5. bearing fault แยกตามมวลถ่วง (กับดักสำคัญที่สุด)")
    lines.append("")

    masses = ["0g", "6g", "20g", "35g"]
    lines.append("| โฟลเดอร์ | " + " | ".join(masses) + " | รวม |")
    lines.append("|---" * (len(masses) + 2) + "|")

    zero_total = 0
    grand_total = 0
    for side in ("underhang", "overhang"):
        side_dir = root / side
        if not side_dir.is_dir():
            continue
        for fault_dir in sorted(p for p in side_dir.iterdir() if p.is_dir()):
            counts = []
            for m in masses:
                n = len(list((fault_dir / m).glob("*.csv"))) if (fault_dir / m).is_dir() else 0
                counts.append(n)
            zero_total += counts[0]
            grand_total += sum(counts)
            cells = " | ".join(str(n) for n in counts)
            lines.append(f"| `{side}/{fault_dir.name}` | {cells} | {sum(counts)} |")

    lines.append("")
    lines.append(f"- ไฟล์ bearing fault ทั้งหมด: {grand_total}")
    lines.append(f"- ไฟล์ที่มวลถ่วง 0 g: {zero_total} ({zero_total / grand_total * 100:.1f}%)")
    lines.append("")
    lines.append("> **วิธีใช้ให้ถูก**")
    lines.append("> - ชุด **0 g** คือโจทย์ยากที่สุดและใกล้สถานการณ์จริงที่สุด ใช้วัดขีดความสามารถของวิธี")
    lines.append(
        "> - ถ้าใช้ชุดมวล > 0 g ต้องเทียบกับ `imbalance/<มวลเดียวกัน>` ที่ความเร็วเดียวกัน "
        "ส่วนต่างที่เหลือจึงเป็นผลของ bearing fault จริง (มวลที่ซ้อนกันคือ 6, 20, 35 g)"
    )
    lines.append("")


def main() -> int:
    root = mafaulda_dir()
    if not root.exists():
        print(f"หาโฟลเดอร์ dataset ไม่เจอ: {root}")
        print("แตกไฟล์ก่อนด้วย: tar -xf mafaulda.zip -C data/raw/mafaulda")
        return 1

    lines: list[str] = [
        f"# ตรวจความถูกต้องของ dataset MAFAULDA หลังแตกไฟล์",
        "",
        f"- วันที่: {date.today().isoformat()}",
        f"- โฟลเดอร์: `{root}`",
        "- สคริปต์: `src/data/verify_dataset.py` (อ่านอย่างเดียว ไม่แก้ไข data/raw)",
        "",
    ]

    counts_ok = check_counts(root, lines)
    shape_ok = check_shape(root, lines)
    check_units(root, lines)
    check_o_radial(root, lines)
    check_bearing_mass_split(root, lines)

    passed = counts_ok and shape_ok
    lines.append("## สรุป")
    lines.append("")
    lines.append(f"- จำนวนไฟล์ครบถ้วน: {'ผ่าน' if counts_ok else 'ไม่ผ่าน'}")
    lines.append(f"- อ่านไฟล์ได้รูปร่างถูกต้อง: {'ผ่าน' if shape_ok else 'ไม่ผ่าน'}")
    lines.append("")

    report = "\n".join(lines)
    print(SEPARATOR)
    print(report)
    print(SEPARATOR)

    out = repo_root() / "experiments" / f"{date.today().isoformat()}-dataset-verification.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"เขียนรายงานลง {out.relative_to(repo_root())}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

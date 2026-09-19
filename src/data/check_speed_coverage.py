"""ตรวจว่าแต่ละคลาสครอบคลุมช่วงความเร็วรอบเท่ากันหรือไม่

**ทำไมต้องตรวจ** ถ้าคลาสหนึ่งมีข้อมูลแต่ช่วงความเร็วต่ำ อีกคลาสมีแต่ช่วงสูง
แล้วเราเอามาเทียบกันหรือเอาไปเทรนรวมกัน โมเดลจะแยกคลาสได้จาก**ความเร็วรอบ**
แทนที่จะแยกจากความเสียหาย ได้ accuracy สูงโดยไม่ได้เรียนรู้สิ่งที่เราต้องการ
เป็นกับดักตระกูลเดียวกับ data leakage และกับดักมวลถ่วงที่บันทึกไว้ใน CLAUDE.md

สคริปต์นี้อ่านแค่**ชื่อไฟล์** ไม่ได้เปิดอ่านข้อมูลข้างใน จึงรันเสร็จในไม่กี่วินาที

รัน:
    python src/data/check_speed_coverage.py
    python src/data/check_speed_coverage.py --max-gap 3.0
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.paths import repo_root  # noqa: E402


def md_table(df: pd.DataFrame, index_name: str = "") -> str:
    """แปลง DataFrame เป็นตาราง markdown

    เขียนเองแทนการใช้ ``DataFrame.to_markdown()`` เพราะตัวนั้นต้องลง
    แพ็กเกจ ``tabulate`` เพิ่ม ซึ่งไม่คุ้มที่จะแบกไปลงบน Raspberry Pi
    เพียงเพื่อจัดรูปแบบตาราง
    """
    def cell(v) -> str:
        if isinstance(v, float):
            return "—" if pd.isna(v) else f"{v:g}"
        return str(v)

    head = [index_name or (df.index.name or "")] + [str(c) for c in df.columns]
    align = ["|---"] + ["|---:" if pd.api.types.is_numeric_dtype(df[c]) else "|---"
                        for c in df.columns]
    out = ["| " + " | ".join(head) + " |", "".join(align) + "|"]
    for idx, row in df.iterrows():
        out.append("| " + " | ".join([f"`{idx}`"] + [cell(v) for v in row]) + " |")
    return "\n".join(out)


def group_key(row: pd.Series) -> str:
    """ชื่อกลุ่มย่อยที่สุดที่มีความหมาย — คือระดับที่มีไฟล์อยู่จริง"""
    parts = [row["cls"]]
    if row["subclass"]:
        parts.append(str(row["subclass"]))
    if row["cls"] in ("underhang", "overhang"):
        parts.append(f"{row['mass_g']}g")
    return "/".join(parts)


def summarise(index: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for name, sub in index.groupby(by, sort=True):
        v = np.sort(sub["rot_hz"].unique())
        gaps = np.diff(v) if len(v) > 1 else np.array([np.nan])
        rows.append({
            "กลุ่ม": name,
            "ไฟล์": len(sub),
            "ความเร็วไม่ซ้ำ": len(v),
            "ต่ำสุด": v.min(),
            "สูงสุด": v.max(),
            "ช่องว่างเฉลี่ย": np.nanmean(gaps),
            "ช่องว่างใหญ่สุด": np.nanmax(gaps),
        })
    return pd.DataFrame(rows).set_index("กลุ่ม").round(3)


def coverage_grid(index: pd.DataFrame, groups: list[str], targets: np.ndarray) -> pd.DataFrame:
    """ตารางระยะห่างจากความเร็วเป้าหมายไปยังไฟล์ที่ใกล้ที่สุดของแต่ละกลุ่ม

    นี่คือตัวเลขที่ใช้จริงตอนจับคู่ไฟล์ข้ามคลาส ถ้าช่องไหนค่าสูง
    แปลว่าที่ความเร็วนั้นกลุ่มนั้นไม่มีข้อมูลใกล้เคียงเลย
    """
    out = {}
    for g in groups:
        v = index.loc[index["_g"] == g, "rot_hz"].to_numpy()
        out[g] = [float(np.min(np.abs(v - t))) for t in targets]
    return pd.DataFrame(out, index=[f"{t:.0f} Hz" for t in targets]).round(2)


def main() -> int:
    ap = argparse.ArgumentParser(description="ตรวจความครอบคลุมของความเร็วรอบ")
    ap.add_argument("--max-gap", type=float, default=3.0,
                    help="ช่องว่างระหว่างความเร็วที่ถือว่ากว้างเกินไป (Hz)")
    ap.add_argument("--step", type=float, default=5.0,
                    help="ระยะห่างของความเร็วเป้าหมายในตารางที่ 3 (Hz)")
    args = ap.parse_args()

    index = mf.build_index()
    index = index.copy()
    index["_g"] = index.apply(group_key, axis=1)

    lines: list[str] = [
        "# ความครอบคลุมของความเร็วรอบในแต่ละคลาส",
        "",
        f"- วันที่: {date.today().isoformat()}",
        f"- สคริปต์: `src/data/check_speed_coverage.py` (อ่านแค่ชื่อไฟล์ ไม่เปิดข้อมูล)",
        f"- เกณฑ์ช่องว่างที่ถือว่ากว้างเกินไป: {args.max_gap} Hz",
        "",
        "## 1. ระดับคลาสหลัก",
        "",
    ]

    per_class = summarise(index, "cls").reindex(mf.CLASS_ORDER)
    lines.append(md_table(per_class, "คลาส"))
    lines.append("")

    overall_lo = index["rot_hz"].min()
    overall_hi = index["rot_hz"].max()
    lines.append(
        f"ทุกคลาสครอบคลุมช่วงเดียวกันคือประมาณ {overall_lo:.1f}–{overall_hi:.1f} Hz "
        f"({overall_lo * 60:.0f}–{overall_hi * 60:.0f} rpm)"
    )
    lines.append("")

    lines.append("## 2. ระดับกลุ่มย่อย (ระดับที่ไฟล์อยู่จริง)")
    lines.append("")
    per_group = summarise(index, "_g")
    lines.append(md_table(per_group, "กลุ่ม"))
    lines.append("")

    wide = per_group[per_group["ช่องว่างใหญ่สุด"] > args.max_gap]
    if wide.empty:
        lines.append(f"✅ ไม่มีกลุ่มไหนมีช่องว่างเกิน {args.max_gap} Hz")
    else:
        lines.append(f"⚠️ **{len(wide)} กลุ่มมีช่องว่างเกิน {args.max_gap} Hz**")
        lines.append("")
        lines.append(md_table(wide[["ไฟล์", "ความเร็วไม่ซ้ำ", "ต่ำสุด", "สูงสุด", "ช่องว่างใหญ่สุด"]], "กลุ่ม"))
    lines.append("")

    lines.append("## 3. ระยะห่างไปยังไฟล์ที่ใกล้ที่สุด เมื่อขอความเร็วเป้าหมาย (Hz)")
    lines.append("")
    lines.append(
        "ตัวเลขคือ |ความเร็วเป้าหมาย − ความเร็วของไฟล์ที่ใกล้ที่สุด| "
        "ยิ่งน้อยยิ่งจับคู่ได้แม่น ค่าที่เกิน 1 Hz แปลว่าที่ความเร็วนั้นกลุ่มนั้นไม่มีข้อมูลใกล้เคียง"
    )
    lines.append("")

    targets = np.arange(
        np.ceil(overall_lo / args.step) * args.step,
        np.floor(overall_hi / args.step) * args.step + 0.1,
        args.step,
    )
    grid = coverage_grid(index, sorted(index["_g"].unique()), targets)
    lines.append(md_table(grid, "ความเร็วเป้าหมาย"))
    lines.append("")

    worst = grid.max()
    lines.append(f"ระยะห่างสูงสุดที่เจอในทั้งตาราง: **{grid.to_numpy().max():.2f} Hz**")
    lines.append("")
    bad_cols = worst[worst > 1.0]
    if not bad_cols.empty:
        lines.append("กลุ่มที่เคยห่างเกิน 1 Hz ที่ความเร็วใดความเร็วหนึ่ง")
        lines.append("")
        lines.append(md_table(bad_cols.round(2).to_frame("ห่างสุด (Hz)"), "กลุ่ม"))
        lines.append("")

    lines.append("## 4. ช่วงความเร็วที่ใช้เทียบได้อย่างยุติธรรม")
    lines.append("")
    lines.append(
        "ถ้าจะเทียบหรือเทรนข้ามกลุ่ม ต้องอยู่ในช่วงที่**ทุกกลุ่มที่เกี่ยวข้องมีข้อมูล** "
        "ไม่งั้นความเร็วจะกลายเป็นตัวแปรที่บอกคลาสได้เอง"
    )
    lines.append("")

    lines.append(
        "> ⚠️ **imbalance ไม่มีไฟล์ที่มวล 0 g เลย** (มีแค่ 6/10/15/20/25/30/35 g) "
        "เพราะ imbalance ที่ 0 กรัมก็คือ normal ดังนั้นการกรอง `mass_g == 0` "
        "จะ**ตัดคลาส imbalance ทิ้งทั้งคลาส** เหลือแค่ 5 คลาส ต้องระวังจุดนี้"
    )
    lines.append("")

    bearing = index["cls"].isin(["underhang", "overhang"])
    bearing_0g = index[~bearing | (index["mass_g"] == 0)]
    light_imb = bearing_0g[
        (bearing_0g["cls"] != "imbalance") | bearing_0g["mass_g"].isin([6, 10, 15, 20])
    ]

    scopes = {
        "ทุกกลุ่มย่อยทั้งหมด": (index, "_g"),
        "bearing 0 g · imbalance รวมเป็นคลาสเดียว": (bearing_0g, "cls"),
        "bearing 0 g · imbalance เฉพาะ 6/10/15/20 g": (light_imb, "_g"),
        "bearing 0 g · imbalance ครบทุกมวล": (bearing_0g, "_g"),
        "mass_g == 0 ล้วน (ตัด imbalance ทิ้ง)": (
            index[(index["mass_g"] == 0) | (index["cls"] == "normal")], "_g"
        ),
    }
    rows = []
    for name, (sub, by) in scopes.items():
        lo = sub.groupby(by)["rot_hz"].min().max()
        hi = sub.groupby(by)["rot_hz"].max().min()
        rows.append({
            "ขอบเขต": name,
            "คลาส": sub["cls"].nunique(),
            "กลุ่ม": sub[by].nunique(),
            "ใช้ได้ตั้งแต่": round(float(lo), 2),
            "ถึง": round(float(hi), 2),
            "กว้าง (Hz)": round(float(hi - lo), 2),
        })
    lines.append(md_table(pd.DataFrame(rows).set_index("ขอบเขต"), "ขอบเขต"))
    lines.append("")
    lines.append(
        "คอลัมน์ **คลาส** คือสิ่งที่ต้องดูก่อน ถ้าไม่ได้ 6 แปลว่าขอบเขตนั้นทำ "
        "6-class classification ไม่ได้ ไม่ว่าช่วงความเร็วจะกว้างแค่ไหน"
    )
    lines.append("")

    # หาช่องว่างภายในที่ใหญ่ที่สุด พร้อมบอกว่าอยู่ตรงไหน
    lines.append("### ช่องว่างภายในที่ใหญ่ที่สุดของแต่ละกลุ่ม (เฉพาะที่เกินเกณฑ์)")
    lines.append("")
    holes = []
    for name, sub in index.groupby("_g"):
        v = np.sort(sub["rot_hz"].unique())
        if len(v) < 2:
            continue
        d = np.diff(v)
        i = int(np.argmax(d))
        if d[i] > args.max_gap:
            holes.append({"กลุ่ม": name, "ช่องว่าง (Hz)": round(float(d[i]), 2),
                          "ตั้งแต่": round(float(v[i]), 3), "ถึง": round(float(v[i + 1]), 3)})
    if holes:
        lines.append(md_table(pd.DataFrame(holes).set_index("กลุ่ม"), "กลุ่ม"))
    else:
        lines.append(f"ไม่มีกลุ่มไหนมีช่องว่างภายในเกิน {args.max_gap} Hz")
    lines.append("")

    # สรุปสำหรับการตัดสินใจ
    lines.append("## สรุป")
    lines.append("")
    n_classes_full = (per_class["ต่ำสุด"] < 13).sum(), (per_class["สูงสุด"] > 61).sum()
    lines.append(
        f"- ทั้ง 6 คลาสเริ่มต่ำกว่า 13 Hz จำนวน {n_classes_full[0]} คลาส "
        f"และไปถึงสูงกว่า 61 Hz จำนวน {n_classes_full[1]} คลาส"
    )
    lines.append(
        f"- กลุ่มย่อยทั้งหมด {len(per_group)} กลุ่ม "
        f"มีช่องว่างเกิน {args.max_gap} Hz อยู่ {len(wide)} กลุ่ม"
    )
    lines.append("")

    report = "\n".join(lines)
    print(report)

    out = repo_root() / "experiments" / f"{date.today().isoformat()}-speed-coverage.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานลง {out.relative_to(repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

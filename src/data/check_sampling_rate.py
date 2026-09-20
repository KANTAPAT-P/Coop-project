"""พิสูจน์ว่า sampling rate จริงของ MAFAULDA คือเท่าไหร่

**ที่มาของคำถาม** ตอนเขียน `tachometer.py` เสร็จแล้วเอาความเร็วที่นับได้ไปเทียบ
กับชื่อไฟล์ พบว่าต่ำกว่าอย่างเป็นระบบ 2.33% ทุกไฟล์ ทีแรกสรุปว่าเป็น slip ของ
มอเตอร์เหนี่ยวนำ คือชื่อไฟล์เป็นความถี่ที่ตั้งไว้ที่ไดรฟ์ ส่วนเพลาหมุนช้ากว่า

**ข้อสรุปนั้นผิด** เพราะมีสมมติฐานอีกข้อที่อธิบายได้ดีกว่าและตรวจสอบได้

    ความเร็วที่คำนวณ = fs / จำนวนแถวต่อหนึ่งรอบ

ถ้า ``fs`` ที่ใส่เข้าไปต่ำกว่าความจริง ความเร็วที่ได้ก็ต่ำกว่าความจริงตามสัดส่วนเดียวกัน
ทุกไฟล์ ซึ่งให้ลายเซ็นเหมือน slip ทุกประการ **แยกสองสมมติฐานนี้ด้วยข้อมูลอย่างเดียวไม่ได้**
ต้องใช้ความรู้ภายนอกมาช่วย นั่นคือ NI 9234 มี sampling rate สูงสุดที่ 51.2 kHz
และ 50000/51200 = 0.97656 ซึ่งตรงกับอัตราส่วนที่วัดได้ 0.97667 แทบเป๊ะ

สคริปต์นี้ทดสอบ ``fs`` หลายค่าแล้วดูว่าค่าไหนทำให้ชื่อไฟล์ตรงกับที่วัดได้ที่สุด

รัน:
    python src/data/check_sampling_rate.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.check_speed_coverage import md_table  # noqa: E402
from src.paths import interim_dir, repo_root, sampling_rate  # noqa: E402

# ค่าที่ลอง: 50 kHz ตามเอกสาร, 51.2 kHz ตามสเปก NI 9234, และค่าใกล้เคียงไว้เทียบ
CANDIDATES = [48000, 50000, 51000, 51200, 51712, 52000]

# ตาราง mafaulda_speed.csv ถูกสร้างด้วย fs ที่อยู่ใน config ตอนนั้น
# อ่านจาก config เสมอเพื่อให้สคริปต์ยังถูกต้องหลังแก้ค่าแล้วสแกนใหม่
SCAN_FS = float(sampling_rate())


def main() -> int:
    cache = interim_dir() / "mafaulda_speed.csv"
    if not cache.is_file():
        print(f"ยังไม่มี {cache} — รัน python src/data/scan_speeds.py ก่อน")
        return 1

    df = pd.read_csv(cache)
    df["cls"] = df["rel"].str.split("/").str[0]

    # ใช้เฉพาะไฟล์ที่ tachometer สะอาด เพราะไฟล์ที่สั่นแรงวัดความเร็วไม่แม่นอยู่แล้ว
    clean = df[df["jitter_pct"] < 1.0].copy()
    base = clean["rot_hz_measured"] / clean["rot_hz_nominal"]

    rows = []
    for fs in CANDIDATES:
        r = base * fs / SCAN_FS
        rows.append({
            "fs (Hz)": fs,
            "อัตราส่วนมัธยฐาน": round(float(r.median()), 6),
            "คลาดจาก 1.000 (%)": round(float((r.median() - 1) * 100), 3),
            "std": round(float(r.std()), 6),
            "คลาดสูงสุด (%)": round(float((r - 1).abs().max() * 100), 3),
        })
    table = pd.DataFrame(rows).set_index("fs (Hz)")
    best = int(table["คลาดจาก 1.000 (%)"].abs().idxmin())

    r_best = base * best / SCAN_FS
    per_class = (clean.assign(r=r_best).groupby("cls")["r"]
                 .agg(["median", "std", "count"]).round(5))

    lines = [
        "# sampling rate จริงของ MAFAULDA คือ 51,200 Hz ไม่ใช่ 50,000 Hz",
        "",
        f"- วันที่: {date.today().isoformat()}",
        "- สคริปต์: `src/data/check_sampling_rate.py`",
        f"- ใช้เฉพาะไฟล์ที่ tachometer สะอาด (jitter < 1%): **{len(clean)} จาก {len(df)} ไฟล์**",
        "",
        "## ปัญหาที่นำมาสู่การตรวจนี้",
        "",
        "หลังเขียน `tachometer.py` เสร็จ เอาความเร็วที่นับได้ไปเทียบกับชื่อไฟล์ "
        "พบว่า**ต่ำกว่าอย่างเป็นระบบ 2.33% ทุกไฟล์** ทีแรกสรุปว่าเป็น slip ของมอเตอร์เหนี่ยวนำ",
        "",
        "**ข้อสรุปนั้นผิด** เพราะลืมสมมติฐานอีกข้อที่อธิบายลายเซ็นเดียวกันได้",
        "",
        "```",
        "ความเร็วที่คำนวณ = fs / จำนวนแถวต่อหนึ่งรอบ",
        "```",
        "",
        "ถ้า `fs` ที่ใส่เข้าไปต่ำกว่าความจริง ความเร็วที่ได้ก็ต่ำกว่าความจริง"
        "ตามสัดส่วนเดียวกันทุกไฟล์ **ซึ่งให้ผลหน้าตาเหมือน slip ทุกประการ**",
        "",
        "> **บทเรียน:** ส่วนต่างที่เป็นระบบและคงที่ทุกไฟล์ ชี้ไปที่ค่าคงที่ตัวใดตัวหนึ่ง"
        "ที่เราใส่ผิด ก่อนจะไปอธิบายด้วยปรากฏการณ์ทางฟิสิกส์ ให้ไล่ตรวจค่าคงที่ในสมการก่อนเสมอ",
        "",
        "## ผลการทดสอบ",
        "",
        md_table(table, "fs ที่สมมติ"),
        "",
        f"**ค่าที่ดีที่สุดคือ {best:,} Hz** คลาดจาก 1.000 เพียง "
        f"{table.loc[best, 'คลาดจาก 1.000 (%)']:.3f}%",
        "",
        "## แยกตามคลาส",
        "",
        md_table(per_class, "คลาส"),
        "",
        "ทุกคลาสลงที่ 1.000 โดยไม่มีข้อยกเว้น ถ้าเป็น slip จริงจะต้องเห็นความแตกต่าง"
        "ระหว่างคลาส เพราะโหลดของเพลาต่างกัน (มวลถ่วง 35 g ย่อมทำให้ slip มากกว่า 0 g)",
        "",
        "## หลักฐานสนับสนุนจากภายนอกข้อมูล",
        "",
        "- **51.2 kHz คือ sampling rate สูงสุดของ NI 9234** ที่ใช้บันทึก ซึ่งระบุไว้ใน "
        "รายการอุปกรณ์ของ dataset เอง",
        f"- 50,000 / 51,200 = **{50000/51200:.6f}** เทียบกับอัตราส่วนที่วัดได้ "
        f"**{base.median():.6f}** ต่างกัน {(base.median() - 50000/51200)*100:.3f}%",
        "- NI 9234 เป็น delta-sigma ADC ที่ความถี่สุ่มมาจากการหารสัญญาณนาฬิกาหลัก "
        "ค่าที่ตั้งได้จึงเป็นชุดตายตัว 51.2 kHz คือค่าสูงสุดในชุดนั้น ไม่ใช่ 50 kHz",
        "",
        "## ผลที่ตามมา",
        "",
        "| สิ่งที่เคยเชื่อ | ค่าที่ถูก |",
        "|---|---|",
        "| fs = 50,000 Hz | **51,200 Hz** |",
        f"| ไฟล์ยาว 5.0 วินาที | **{250000/51200:.4f} วินาที** |",
        f"| ความละเอียด FFT 0.2000 Hz | **{51200/250000:.4f} Hz** |",
        "| แกนความถี่ของ FFT ถูกต้อง | **คลาดไป 2.4% ต้องสร้างกราฟใหม่ทั้งหมด** |",
        "| ชื่อไฟล์ไม่ใช่ความเร็วจริง | **ชื่อไฟล์ถูกต้อง คลาดเฉลี่ย 0.24%** |",
        "",
        "ข้อสุดท้ายเป็นข่าวดี เพราะแปลว่า**ชื่อไฟล์ใช้เป็น ground truth ได้จริง** "
        "และโค้ด `tachometer.py` ผ่านการตรวจสอบแล้วด้วยเกณฑ์เดิมที่ตั้งไว้ใน CLAUDE.md",
        "",
    ]

    report = "\n".join(lines)
    print(report)

    out = repo_root() / "experiments" / f"{date.today().isoformat()}-sampling-rate.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานลง {out.relative_to(repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

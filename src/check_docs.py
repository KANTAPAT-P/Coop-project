"""ตรวจว่าเอกสาร .md ยังตรงกับโค้ดและข้อมูลจริงหรือไม่

## ทำไมต้องมี

`CLAUDE.md` กฎข้อ 6 บอกว่าต้องไล่ตรวจเอกสารทุกครั้งที่ปิด checkpoint
แต่กฎที่ต้องอาศัยความขยันของคนจะถูกลืมเสมอ สคริปต์นี้ทำส่วนที่ตรวจด้วยเครื่องได้

**เจอมาแล้วจริง** ตอนไล่ตรวจด้วยมือเมื่อ 2026-10-05 พบเอกสารล้าหลัง 10 ไฟล์
รวมถึง `README.md` ที่ยังเขียนว่าพัลส์ tachometer กว้าง 20 แถว ทั้งที่
`CLAUDE.md` แก้เป็น 443 แถวไปนานแล้ว และเอกสารที่**ขัดกันเองในไฟล์เดียวกัน**

## 🚨 ออกแบบให้เตือนผิดน้อยที่สุด เพราะเครื่องมือที่เตือนพร่ำเพรื่อจะถูกปิดทิ้ง

นี่เป็นบทเรียนเดียวกับระบบแจ้งเตือนเครื่องจักรใน `src/models/detector.py`
**ระบบที่เตือนบ่อยเกินไปจะถูกคนหน้างานปิดทิ้งภายในสัปดาห์เดียว**
เครื่องมือตรวจเอกสารก็เหมือนกัน ถ้ามันบ่นทุกครั้งที่รัน คนจะเลิกรัน

จึงแบ่งการตรวจเป็นสามระดับตามความแน่นอนของมัน

| ระดับ | ตรวจอะไร | ผิดพลาดได้ไหม | ทำให้ล้มเหลว |
|---|---|---|---|
| **ERROR** | path และลิงก์ที่ชี้ไปยังไฟล์ที่ไม่มีอยู่ | **ไม่ได้เลย** | ✅ |
| **ERROR** | ตัวเลขที่ยึดกับวลีเฉพาะ เทียบกับค่าที่คำนวณจากของจริง | แทบไม่ได้ | ✅ |
| **WARN** | ค่าเก่าที่เคยแก้แล้ว ซึ่งอาจโผล่กลับมา | **ได้** เพราะบางที่พูดถึงค่าเก่าโดยเจตนา | ❌ ต้องใส่ `--strict` |

สองระดับแรกคำนวณจากแหล่งความจริงโดยตรง จึงฟันธงได้
ส่วนระดับที่สามเป็นการค้นรูปแบบ ซึ่งแยกไม่ออกระหว่าง "เขียนผิด" กับ
"ยกค่าเก่ามาอธิบายว่าทำไมถึงผิด" จึงเป็นแค่คำเตือนให้คนไปดู

## ไม่ตรวจ `experiments/`

เพราะเป็น**บันทึกลงวันที่** ตัวเลขในนั้นคือสิ่งที่วัดได้ ณ วันนั้น
การแก้ให้เป็นปัจจุบันจะทำลายจุดประสงค์ของมัน และทำให้ย้อนดูไม่ได้ว่า
ตอนนั้นเข้าใจอย่างไร

รัน:
    python src/check_docs.py
    python src/check_docs.py --strict     # ให้คำเตือนทำให้ล้มเหลวด้วย
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.paths import repo_root, sampling_rate  # noqa: E402

N_ROWS = 250_000          # แถวต่อไฟล์ของ MAFAULDA เป็นค่าตายตัวของชุดข้อมูล

# เอกสารที่ต้องสดเสมอ — ไม่รวม experiments/ ด้วยเหตุผลที่อธิบายไว้ข้างบน
LIVING = [
    "README.md", "CLAUDE.md",
    "docs/*.md", "paper/*.md", "stack/README.md",
    "reports/*/README*.md",
]


# --------------------------------------------------------------- ผลการตรวจ

@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    checked: int = 0

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warns.append(f"{where}: {msg}")


# ------------------------------------------------------- แหล่งความจริง

def living_docs() -> list[Path]:
    root = repo_root()
    out: list[Path] = []
    for pat in LIVING:
        out.extend(sorted(root.glob(pat)))
    return [p for p in out if p.is_file()]


def truth_panels() -> int | None:
    """จำนวนแผงใน Grafana อ่านจากไฟล์แดชบอร์ดที่สร้างจริง"""
    p = repo_root() / "stack" / "grafana" / "dashboards" / "pdm-overview.json"
    if not p.is_file():
        return None
    return len(json.loads(p.read_text(encoding="utf-8"))["panels"])


def truth_model() -> dict | None:
    """ค่าจากโมเดลที่เทรนแล้ว — ไม่ขึ้น git จึงอาจไม่มี"""
    p = repo_root() / "models" / "baseline-normal.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def truth_dataset_files() -> int | None:
    """จำนวนไฟล์ใน MAFAULDA นับจากตารางที่สกัดแล้ว ซึ่งเร็วกว่าไล่ rglob"""
    p = repo_root() / "data" / "processed" / "feature_grid.csv"
    if not p.is_file():
        return None
    with p.open(encoding="utf-8") as f:
        return sum(1 for _ in f) - 1          # ลบบรรทัดหัวตาราง


def truth_measurements() -> list[str]:
    """ชื่อ measurement ที่ `ingest.py` เขียนลง InfluxDB จริง"""
    p = repo_root() / "src" / "service" / "ingest.py"
    if not p.is_file():
        return []
    src = p.read_text(encoding="utf-8")
    return re.findall(r'^[A-Z_]*MEASUREMENT\s*=\s*"([a-z_]+)"', src, re.M)


# ------------------------------------------------- 1) path และลิงก์

# path ที่เขียนใน backtick เช่น `src/models/detector.py`
RE_BACKTICK = re.compile(
    r"`((?:src|docs|stack|reports|experiments|paper|models|data|notebooks)"
    r"/[\w\-./]+?)`")
# ลิงก์ markdown ที่ชี้ไปยังไฟล์ในโปรเจกต์
RE_MDLINK = re.compile(r"\[[^\]]*\]\(([^)#:]+?)\)")


def check_paths(doc: Path, text: str, rep: Report) -> None:
    root = repo_root()
    rel = doc.relative_to(root)
    for m in set(RE_BACKTICK.findall(text)):
        q = m.rstrip("/.")
        if "*" in q or "<" in q:
            continue
        if not (root / q).exists():
            rep.error(str(rel), f"path ไม่มีอยู่จริง  `{q}`")
    for m in set(RE_MDLINK.findall(text)):
        if m.startswith(("http", "mailto:", "#")) or "*" in m or "<" in m:
            continue
        target = (doc.parent / m).resolve()
        if not target.exists():
            rep.error(str(rel), f"ลิงก์เสีย  ({m})")


# ------------------------------------- 2) ตัวเลขที่ยึดกับวลีเฉพาะ

@dataclass
class Anchored:
    """ข้ออ้างตัวเลขที่ผูกกับวลีเฉพาะจนไม่กำกวม

    ``pattern`` ต้องจับกลุ่มเดียวคือตัวเลข และต้องมีคำรอบข้างมากพอ
    ที่จะไม่ไปชนกับตัวเลขอื่นที่บังเอิญเท่ากัน
    """

    label: str
    pattern: re.Pattern
    truth: float | int | None
    fmt: str = "{:g}"


def anchored_checks() -> list[Anchored]:
    fs = float(sampling_rate())
    model = truth_model()
    out = [
        Anchored("sampling rate",
                 re.compile(r"sampling rate จริงคือ ([\d,]+) Hz"), fs),
        # ⚠️ เคยมีการตรวจ "ความละเอียด FFT" ตรงนี้ แล้ว**ตัดออก**
        #
        # เพราะวลีนี้ปรากฏทั้งในที่ที่ระบุค่าที่ถูก (0.2048) และในตารางที่
        # ยกค่าเก่า (0.2000) มาเทียบว่าผิดอย่างไร ซึ่งแยกด้วย regex ไม่ได้
        # โดยไม่เสี่ยงเตือนผิด **และเครื่องมือที่เตือนผิดจะถูกปิดทิ้ง**
        # ค่า fs ที่เป็นต้นตอของตัวเลขนี้ถูกตรวจไปแล้วในรายการแรกอยู่ดี
        Anchored("จำนวนไฟล์ใน dataset",
                 re.compile(r"([\d,]+) ไฟล์ลง `data/raw/mafaulda/`"),
                 truth_dataset_files()),
        Anchored("จำนวนแผง Grafana",
                 re.compile(r"แดชบอร์ด[^|\n]*?ตอนนี้ (\d+) แผง"),
                 truth_panels()),
    ]
    if model:
        out += [
            # 🚩 ``(?!อย่าง)`` สำคัญมาก
            #
            # รอบแรกใช้ ``จาก (\d+) ตัว`` เฉยๆ ซึ่งไปจับ "จาก 47 **ตัวอย่าง**"
            # ด้วย เพราะ "ตัว" เป็นคำนำหน้าของ "ตัวอย่าง" แล้วรายงานว่า
            # จำนวนตัวชี้วัดผิดทั้งที่บรรทัดนั้นพูดถึงจำนวนตัวอย่าง
            #
            # รอบที่สองแก้เป็น ``จากทั้งหมด`` ซึ่ง**แย่กว่าเดิม** เพราะวลีนั้น
            # ไม่มีอยู่ในเอกสารเลย ตัวตรวจจึงตายเงียบๆ โดยไม่มีใครรู้
            #
            # **ตัวตรวจที่ไม่เคยจับอะไรได้ อันตรายกว่าตัวตรวจที่เตือนผิด**
            # เพราะมันให้ความมั่นใจปลอมๆ จึงต้องทดสอบด้วยการแกล้งทำให้ผิด
            # ทุกครั้งที่เพิ่มหรือแก้ pattern
            Anchored("จำนวนตัวชี้วัด",
                     re.compile(r"จาก(?:ทั้งหมด)? (\d+) ตัวชี้วัด"),
                     len(model["features"])),
            Anchored("เกณฑ์ vote_min",
                     re.compile(r"เกณฑ์เตือน = (\d+) "),
                     model["vote_min"]),
        ]
    return out


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def check_anchored(doc: Path, text: str, checks: list[Anchored],
                   rep: Report) -> None:
    rel = doc.relative_to(repo_root())
    for c in checks:
        if c.truth is None:
            continue
        for found in c.pattern.findall(text):
            try:
                got = _num(found)
            except ValueError:
                continue
            if abs(got - float(c.truth)) > 1e-6:
                rep.error(str(rel),
                          f"{c.label} เขียนว่า {found} "
                          f"แต่ของจริงคือ {c.fmt.format(c.truth)}")


# --------------------------------------------- 3) ค่าเก่าที่เคยแก้แล้ว

@dataclass
class Stale:
    """ค่าที่เคยเขียนผิดแล้วแก้ไปแล้ว ซึ่งไม่ควรโผล่กลับมาเป็นค่าปัจจุบัน"""

    label: str
    pattern: re.Pattern
    correct: str
    # ถ้าบรรทัดนั้นมีคำเหล่านี้ แปลว่ากำลังพูดถึงค่าเก่าโดยเจตนา
    ok_markers: tuple[str, ...]


# คำที่บ่งว่าบรรทัดนั้นกำลังอธิบายว่าค่าเก่าผิด ไม่ได้ใช้ค่าเก่าเป็นข้อเท็จจริง
PAST = ("ไม่ใช่", "ผิด", "เคย", "เดิม", "ต้นทาง", "คลาด", "❌", "🚩", "🚨",
        "ฉบับ", "ซ้ำความ", "แก้", "ที่ถูก", "จริงคือ", "ลงตัว", "สมมติ",
        "อัตราส่วน", "ขัดกัน", "ต่ำไป", "เทียบ", "ยังเขียน", "สุ่มได้",
        "ตามเอกสาร", "ระบุ", "ไม่ได้ตั้งแต่ต้น", "ประมาณไว้")


def _is_comparison(line: str, correct: str) -> bool:
    """บรรทัดนี้กำลังเทียบค่าเก่ากับค่าใหม่อยู่หรือไม่

    สองรูปแบบที่เจอบ่อยและไม่ใช่ความผิดพลาด

    * **แถวตาราง** ที่มีทั้งค่าเก่าและค่าใหม่อยู่ในบรรทัดเดียว
      เช่น ``| fs = 50,000 Hz | **51,200 Hz** |``
    * **ข้อความที่ยกมาจากงานวิจัย** ซึ่งเป็นหน้าที่ของ
      ``paper/literature-review.md`` ที่จะรายงานว่าเขาเขียนอะไร
      ไม่ใช่ข้อผิดพลาดของเรา
    """
    if line.lstrip().startswith("|"):
        # **แถวตารางทุกแถว** ไม่ใช่เฉพาะแถวที่มีค่าที่ถูกอยู่ด้วย
        #
        # เพราะตารางเทียบค่าผู้สมัครหลายค่าจะมีแถวละหนึ่งค่า เช่น
        # ``| 50,000 Hz | 0.976650 | −2.33% |`` ซึ่งเป็นแถวข้อมูลของ
        # การทดสอบว่า fs ค่าไหนถูก ไม่ใช่การยืนยันว่า 50,000 คือค่าที่ใช้
        #
        # ยอมแลกความไวตรงนี้ เพราะข้อเท็จจริงเชิงตัวเลขที่สำคัญถูกตรวจ
        # แบบฟันธงไปแล้วในชั้น ERROR ส่วนชั้นนี้เป็นเพียงตาข่ายรองรับ
        return True
    return '*"' in line or line.lstrip().startswith("> *")


def stale_checks() -> list[Stale]:
    return [
        Stale("อัตราการสุ่ม",
              re.compile(r"\b50[,.]?000 Hz\b|\b50 ?kHz\b"),
              "51,200 Hz", PAST),
        Stale("ความกว้างพัลส์ tachometer",
              re.compile(r"พัลส์กว้าง(?:ราว)? 20 แถว"),
              "2.4–8.9 ms = สูงสุด 443 แถว", PAST),
        Stale("ขนาดข้อความ",
              re.compile(r"1\.8 ?(?:กิโลไบต์|kB|KB)"),
              "2,254 ไบต์", PAST),
        Stale("ความอ่อนของ o_radial",
              re.compile(r"ราว 5% ของช่องอื่น"),
              "0.050–0.498 เท่า ต่างกันเอง 10 เท่า", PAST),
    ]


def check_stale(doc: Path, text: str, checks: list[Stale],
                rep: Report) -> None:
    rel = doc.relative_to(repo_root())
    for i, line in enumerate(text.splitlines(), start=1):
        for c in checks:
            if not c.pattern.search(line):
                continue
            if any(mk in line for mk in c.ok_markers):
                continue          # บรรทัดนี้พูดถึงค่าเก่าโดยเจตนา
            if _is_comparison(line, c.correct):
                continue
            rep.warn(f"{rel}:{i}",
                     f"{c.label} อาจเป็นค่าเก่า — ของจริงคือ {c.correct}\n"
                     f"      {line.strip()[:100]}")


# ------------------------------------ 4) measurement ต้องถูกบันทึกไว้

def check_measurements(rep: Report) -> None:
    """ทุก measurement ที่โค้ดเขียนจริง ต้องมีอธิบายไว้ในเอกสารออกแบบ

    กันกรณีที่เพิ่ม measurement ใหม่ในโค้ดแล้วลืมเขียนเอกสาร ซึ่งเกิดขึ้นจริง
    กับ `assessment` ตอนทำขั้นที่ 5 ของ Checkpoint 3
    """
    names = truth_measurements()
    if not names:
        return
    doc = repo_root() / "docs" / "data-pipeline-design.md"
    if not doc.is_file():
        return
    text = doc.read_text(encoding="utf-8")
    for n in names:
        if n not in text:
            rep.error("docs/data-pipeline-design.md",
                      f"measurement `{n}` มีในโค้ดแต่ไม่มีในเอกสาร")


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="ตรวจว่าเอกสาร .md ยังตรงกับโค้ดและข้อมูลจริง")
    ap.add_argument("--strict", action="store_true",
                    help="ให้คำเตือนทำให้ล้มเหลวด้วย")
    args = ap.parse_args()

    rep = Report()
    docs = living_docs()
    anchored = anchored_checks()
    stale = stale_checks()

    for d in docs:
        text = d.read_text(encoding="utf-8")
        rep.checked += 1
        check_paths(d, text, rep)
        check_anchored(d, text, anchored, rep)
        check_stale(d, text, stale, rep)
    check_measurements(rep)

    print(f"ตรวจเอกสารที่ต้องสด {rep.checked} ไฟล์ "
          f"(ไม่รวม experiments/ ซึ่งเป็นบันทึกลงวันที่)")
    print()
    print("แหล่งความจริงที่ใช้เทียบ")
    model = truth_model()
    rows = [
        ("sampling rate", f"{float(sampling_rate()):,.0f} Hz", "config.yaml"),
        ("ความละเอียด FFT", f"{float(sampling_rate())/N_ROWS:.4f} Hz", "คำนวณ"),
        ("ไฟล์ใน dataset", truth_dataset_files(), "feature_grid.csv"),
        ("แผง Grafana", truth_panels(), "pdm-overview.json"),
        ("ตัวชี้วัด", len(model["features"]) if model else None,
         "baseline-normal.json"),
        ("เกณฑ์ vote_min", model["vote_min"] if model else None,
         "baseline-normal.json"),
        ("measurement", ", ".join(truth_measurements()) or None, "ingest.py"),
    ]
    for name, val, src in rows:
        mark = "" if val is not None else "   (ไม่พบ ข้ามการตรวจที่ใช้ค่านี้)"
        print(f"  {name:18s} {str(val):28s} <- {src}{mark}")
    print()

    if rep.errors:
        print(f"❌ ผิดพลาด {len(rep.errors)} จุด")
        for e in rep.errors:
            print(f"   {e}")
        print()
    if rep.warns:
        print(f"⚠️ คำเตือน {len(rep.warns)} จุด "
              f"(อาจเป็นการเตือนผิด ต้องอ่านเองก่อนแก้)")
        for w in rep.warns:
            print(f"   {w}")
        print()

    if rep.errors:
        return 1
    if rep.warns and args.strict:
        print("ล้มเหลวเพราะใส่ --strict")
        return 1
    if not rep.warns:
        print("✅ ไม่พบปัญหา")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

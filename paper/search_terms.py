"""ค้นคำสำคัญในไฟล์ PDF ทั้ง 12 ฉบับ เพื่อตรวจคำเคลมแบบ "0 จาก 12 ฉบับ"

## ทำไมต้องมี

`docs/pipeline-walkthrough.md` หัวข้อเทียบวรรณกรรมเคลมว่า **ไม่มีฉบับใดทำ**
หลายเรื่อง เช่น envelope analysis, การยืนยันซ้ำตามเวลา, การทดสอบแนวโน้ม

> **คำเคลมว่า "ไม่มีใครทำ" แข็งกว่าคำเคลมว่า "มีคนทำ" เสมอ**
> เพราะต้องตรวจทุกฉบับ ไม่ใช่หาเจอฉบับเดียวก็จบ
> ดังนั้นมันต้องตรวจด้วยเครื่อง ไม่ใช่ความจำจากการอ่าน

สคริปต์นี้แปลง PDF เป็นข้อความแล้วค้นคำ **เพื่อให้คำเคลมในเอกสารตรวจซ้ำได้**

## ⚠️ ข้อจำกัดที่ต้องรู้ก่อนเชื่อผล

1. **การสกัดข้อความจาก PDF ไม่สมบูรณ์** สมการ ตาราง และอักษรควบมักเพี้ยน
   → **"ไม่เจอ" ไม่ได้พิสูจน์ว่า "ไม่มี"** ต้องยืนยันด้วยการอ่านอีกชั้น
2. **เจอคำไม่ได้แปลว่าเขาทำ** เคยเจอมาแล้วสองกรณี
   - ฉบับ 04 มีคำ `envelope` และ `Hilbert` แต่อยู่ในหัวข้อ related work
     ที่เล่าถึงงานของคนอื่น
   - ฉบับ 09 มีคำ `1X` แต่เป็นเศษจากสูตร `b-1X j=0` ที่สกัดออกมาเพี้ยน
   → **ทุกผลที่เจอต้องเปิดดูบริบทก่อนสรุป** สคริปต์จึงพิมพ์บริบทรอบคำให้ด้วย

รัน:
    python paper/search_terms.py                 # ชุดคำที่ใช้ตรวจเอกสาร
    python paper/search_terms.py envelope BPFO   # ค้นคำที่ระบุเอง
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:                                   # pragma: no cover
    try:
        from PyPDF2 import PdfReader                  # type: ignore
    except ImportError:
        raise SystemExit(
            "ต้องมี pypdf ก่อน\n  pip install pypdf")

PAPER_DIR = Path(__file__).resolve().parent

# กลุ่มคำที่ใช้ตรวจคำเคลมในเอกสาร — (ชื่อกลุ่ม, คำที่ค้น)
GROUPS: list[tuple[str, list[str]]] = [
    ("envelope / ความถี่ความเสียหายตลับลูกปืน",
     ["envelope", "hilbert", "bpfo", "bpfi", "ball pass", "cage frequency",
      "characteristic frequency", "sideband", "spectral kurtosis", "kurtogram"]),
    ("order tracking / angular resampling",
     ["order tracking", "angular resampl", "revolution-synchronous",
      "synchronous averaging", "phase variable"]),
    ("การยืนยันซ้ำตามเวลา",
     ["consecutive", "persistence", "debounce", "k of m", "k-of-m",
      "hysteresis", "dwell time"]),
    ("อัตราการเตือนผิดและความหน่วง",
     ["false alarm", "false alert", "alarms per", "per day",
      "detection delay", "detection latency", "time to detect"]),
    ("การทดสอบแนวโน้ม",
     ["mann-kendall", "mann kendall", "trend test", "sen's slope",
      "sens slope", "degradation trend", "prognos"]),
    ("ช่องปฏิเสธ / ตรวจไม่ได้",
     ["unknown anomaly", "open-set", "open set", "reject option",
      "indeterminate", "abstain"]),
    ("การส่งและการเก็บข้อมูล",
     ["mqtt", "broker", "influxdb", "grafana", "retention", "qos"]),
    ("ฮาร์ดแวร์เป้าหมาย",
     ["raspberry", "esp32", "microcontroller", "stm32", "mcu"]),
]


def pdf_text(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:                          # pragma: no cover
        print(f"  ⚠️ อ่าน {path.name} ไม่ได้: {exc}")
        return ""
    out = []
    for page in reader.pages:
        try:
            out.append(page.extract_text() or "")
        except Exception:
            out.append("")
    return "\n".join(out)


def short(name: str, width: int = 44) -> str:
    return name[:width - 1] + "…" if len(name) > width else name


def main() -> int:
    pdfs = sorted(PAPER_DIR.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"ไม่พบไฟล์ PDF ใน {PAPER_DIR}")

    print(f"อ่าน {len(pdfs)} ฉบับ")
    texts: dict[str, str] = {}
    for p in pdfs:
        texts[p.name] = pdf_text(p).lower()
        print(f"  {len(texts[p.name]):>8,} ตัวอักษร  {short(p.name)}")
    print()

    if len(sys.argv) > 1:
        groups = [("คำที่ระบุเอง", [a.lower() for a in sys.argv[1:]])]
    else:
        groups = GROUPS

    for title, terms in groups:
        print("=" * 78)
        print(f"  {title}")
        print("=" * 78)
        for term in terms:
            hits = {n: t.count(term) for n, t in texts.items() if term in t}
            if not hits:
                print(f"  {term:28s} ไม่เจอในฉบับใดเลย  (0 / {len(pdfs)})")
                continue
            print(f"  {term:28s} เจอใน {len(hits)} / {len(pdfs)} ฉบับ")
            for n, c in sorted(hits.items(), key=lambda kv: -kv[1]):
                print(f"      {c:>3}x  {short(n)}")
                # พิมพ์บริบทให้ดู เพราะ "เจอคำ" ไม่ได้แปลว่า "เขาทำ"
                m = re.search(r".{0,70}" + re.escape(term) + r".{0,70}",
                              texts[n], re.S)
                if m:
                    ctx = " ".join(m.group(0).split())
                    print(f"            ...{ctx}...")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

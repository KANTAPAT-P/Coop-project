"""พิสูจน์ sampling rate ของ MAFAULDA จากชื่อไฟล์ โดยไม่อ่านข้อมูลเลย

**ทำไมต้องมีสคริปต์นี้ ทั้งที่มี `check_sampling_rate.py` อยู่แล้ว**

สคริปต์เดิมพิสูจน์ด้วยการนับพัลส์ tachometer แล้วเทียบกับชื่อไฟล์ ซึ่งแข็งพอ
แต่**พึ่งโค้ดที่เราเขียนเอง** (`tachometer.py`) และพึ่งสมมติฐานว่าชื่อไฟล์คือ
ความเร็วจริงไม่ใช่ค่าที่ตั้งไว้ ถ้ามีคนแย้งว่าโค้ดนับพัลส์ผิด หรือแย้งว่าชื่อไฟล์
เป็นค่า setpoint ที่ต่างจากความเร็วจริงเพราะ slip เราจะเถียงยาก

สคริปต์นี้ปิดช่องนั้นด้วยการพิสูจน์ที่**ไม่อ่านข้อมูลแม้แต่แถวเดียว**

**หลักการ** ถ้าคนทำ dataset หาความเร็วรอบด้วย FFT ของช่อง tachometer บนทั้งไฟล์
(250,000 แถว) แล้วตั้งชื่อไฟล์ตามความถี่ของช่อง (bin) ที่เจอ ชื่อไฟล์ทุกไฟล์
ต้องเป็น **จำนวนเต็มเท่าของความละเอียด FFT** ซึ่งเท่ากับ ``fs / 250000``

    fs = 51,200  ->  0.2048 Hz
    fs = 50,000  ->  0.2000 Hz

ค่า 0.2048 เกิดจาก ``fs/N`` ซึ่งเป็นสมบัติของ**การประมวลผลสัญญาณ** ไม่ใช่สมบัติ
ของมอเตอร์ ดังนั้นถ้าชื่อไฟล์ลงตัวกับ 0.2048 ครบทุกไฟล์ จะอธิบายด้วยอย่างอื่นไม่ได้
นอกจากว่าชื่อไฟล์ถูกคำนวณจากข้อมูลที่สุ่มมาที่ 51,200 Hz

**ผลที่ได้ (2026-10-02)** ลงตัว 246 จาก 246 ชื่อ = 100.00% ที่ 0.2048 Hz
ขณะที่ 0.2000 Hz ลงตัวเพียง 2 ชื่อ = 0.81%
รายละเอียดใน ``experiments/2026-10-02-sampling-rate-filename-proof.md``

รัน:
    python src/data/check_fs_from_filenames.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import raw_dir, sampling_rate  # noqa: E402

# จำนวนแถวต่อไฟล์ของ MAFAULDA เป็นค่าตายตัวของ dataset ไม่ได้มาจาก config
# เพราะมันคือความยาวของไฟล์ ไม่ใช่การตั้งค่าของเรา
N_ROWS = 250_000

# ค่าที่ลอง: 50 kHz ตามเอกสารต้นทาง, 51.2 kHz ตามสเปก NI 9234, และค่าอื่นไว้เทียบ
# ใส่ค่าที่ "ไม่ควรเข้า" ไว้ด้วย เพื่อให้เห็นว่าการทดสอบนี้แยกแยะได้จริง
# ไม่ใช่ลงตัวกับทุกค่า
CANDIDATES = [48000, 50000, 51000, 51200, 51712, 52000, 65536]

# ยอมให้ค่าคลาดจากจำนวนเต็มได้เท่านี้ ตั้งให้เข้มเพราะชื่อไฟล์เป็นทศนิยม
# ไม่เกิน 4 ตำแหน่ง ถ้าลงตัวจริงจะลงตัวแบบไม่มีเศษเลย
TOL = 1e-6


def unique_speed_names() -> list[str]:
    """ชื่อไฟล์ (ไม่รวมนามสกุล) ที่ไม่ซ้ำกัน จากทั้ง dataset

    ต้องใช้ ``rglob`` เพราะโฟลเดอร์ bearing fault มีชั้นย่อยเป็นมวลถ่วงอีกชั้น
    ถ้าใช้ ``glob`` จะได้ศูนย์ไฟล์
    """
    root = raw_dir() / "mafaulda"
    if not root.is_dir():
        raise SystemExit(f"ไม่พบโฟลเดอร์ dataset ที่ {root}")
    return sorted({p.stem for p in root.rglob("*.csv")})


def divisibility(names: list[str], fs: float) -> tuple[float, int, list[tuple[str, float]]]:
    """นับว่าชื่อไฟล์กี่ชื่อเป็นจำนวนเต็มเท่าของความละเอียด FFT ที่ fs นี้"""
    bin_hz = fs / N_ROWS
    ok = 0
    bad: list[tuple[str, float]] = []
    for name in names:
        try:
            value = float(name)
        except ValueError:
            continue  # ชื่อไฟล์ที่ไม่ใช่ตัวเลข ถ้ามี
        k = value / bin_hz
        if abs(k - round(k)) < TOL:
            ok += 1
        else:
            bad.append((name, k))
    return bin_hz, ok, bad


def main() -> int:
    names = unique_speed_names()
    print(f"ชื่อไฟล์ที่ไม่ซ้ำกัน {len(names)} ชื่อ "
          f"(ช่วง {min(float(n) for n in names):.4f} - {max(float(n) for n in names):.4f} Hz)")
    print(f"จำนวนแถวต่อไฟล์ {N_ROWS:,}")
    print()
    print(f"{'fs ที่สมมติ':>12} {'ความละเอียด FFT':>18} {'ชื่อไฟล์ที่ลงตัว':>20}")
    print("-" * 56)

    best: tuple[int, int] = (-1, 0)  # (ok, fs)
    for fs in CANDIDATES:
        bin_hz, ok, _ = divisibility(names, fs)
        pct = 100.0 * ok / len(names)
        mark = "  <== ลงตัวทั้งหมด" if ok == len(names) else ""
        print(f"{fs:>12,} {bin_hz:>15.6f} Hz {ok:>12,}/{len(names)} = {pct:6.2f}%{mark}")
        if ok > best[0]:
            best = (ok, fs)
    print("-" * 56)

    ok, fs_best = best
    print()
    if ok != len(names):
        print("⚠️ ไม่มีค่า fs ใดที่ทำให้ชื่อไฟล์ลงตัวครบทุกไฟล์")
        print("   แปลว่าสมมติฐานว่าชื่อไฟล์มาจากช่อง FFT อาจไม่ถูก ต้องตรวจเพิ่ม")
        return 1

    print(f"✅ fs = {fs_best:,} Hz ทำให้ชื่อไฟล์ลงตัวครบทั้ง {len(names)} ชื่อ")

    configured = float(sampling_rate())
    if abs(configured - fs_best) < 1.0:
        print(f"✅ ตรงกับค่าใน config.yaml ({configured:,.0f} Hz)")
    else:
        print(f"🚨 ไม่ตรงกับค่าใน config.yaml ({configured:,.0f} Hz) "
              f"— ต้องแก้ config ให้เป็น {fs_best:,} Hz")
        return 1

    # แสดงตัวอย่างให้เห็นว่าได้จำนวนเต็มเรียงติดกัน ซึ่งเป็นหลักฐานที่ดูง่ายที่สุด
    bin_hz = fs_best / N_ROWS
    other = 50000 / N_ROWS
    print()
    print(f"ตัวอย่าง ชื่อไฟล์หารด้วยความละเอียด FFT")
    print(f"{'ชื่อไฟล์':>12} {'/ ' + format(bin_hz, '.4f'):>12} {'/ ' + format(other, '.4f'):>12}")
    sample = names[:5] + names[len(names) // 2: len(names) // 2 + 3] + names[-3:]
    for name in sample:
        value = float(name)
        print(f"{name:>12} {value / bin_hz:>12.4f} {value / other:>12.4f}")
    print()
    print("คอลัมน์กลางได้จำนวนเต็มเรียงติดกัน คอลัมน์ขวาไม่ลงตัวเลย")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

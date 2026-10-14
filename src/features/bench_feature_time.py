"""จับเวลาการสกัดตัวชี้วัดหนึ่งหน้าต่าง เพื่อประมาณภาระงานบน ESP32

## ข้อจำกัดที่ต้องอ่านก่อนใช้ตัวเลข

**สคริปต์นี้วัดบนโน้ตบุ๊ก ไม่ได้วัดบน ESP32** ตัวเลขที่ได้จึงเป็น
**จุดตั้งต้นสำหรับประมาณ ไม่ใช่คำตอบ** เวลาจริงบนไมโครคอนโทรลเลอร์
ขึ้นกับหลายอย่างที่โน้ตบุ๊กไม่มี เช่นไลบรารี FFT ที่ใช้คำสั่งพิเศษของชิป
การแย่งซีพียูกับสแตก WiFi และความเร็วหน่วยความจำ

`CLAUDE.md` หัวข้อ 7 ระบุว่า "เวลาสกัด feature บน MCU" เป็นหนึ่งใน
**สองข้อที่ยังไม่มีใครตอบ รวมทั้งงานวิจัยทั้ง 12 ฉบับที่ทบทวนแล้ว**
สคริปต์นี้จึงไม่ได้ปิดช่องว่างนั้น เพียงแต่ทำให้ประมาณได้อย่างมีฐาน

## สิ่งที่สคริปต์นี้ตอบได้จริง

1. **งานส่วนใดหนักที่สุด** ซึ่งไม่ขึ้นกับว่ารันบนเครื่องใด
2. **หน่วยความจำที่ต้องใช้** ซึ่งคำนวณจากขนาดบัฟเฟอร์โดยตรง
   และเป็นข้อจำกัดที่น่ากังวลกว่าความเร็ว

รัน:
    python src/features/bench_feature_time.py
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda                                  # noqa: E402
from src.features import spectral                              # noqa: E402
from src.features.screen_signatures import channel_features    # noqa: E402
from src.paths import sampling_rate                            # noqa: E402

N_CHANNELS = 6          # ช่องสั่นสะเทือนที่ใช้สกัดตัวชี้วัด
PERIOD_MS = 10_000.0    # คาบการส่ง 10 วินาที = งบเวลาที่มีจริงต่อหนึ่งหน้าต่าง


def bench(fn, repeat: int = 20) -> float:
    """คืนเวลาเฉลี่ยเป็นมิลลิวินาที โดยไม่นับรอบแรกซึ่งยังไม่อุ่นเครื่อง"""
    fn()
    t0 = time.perf_counter()
    for _ in range(repeat):
        fn()
    return (time.perf_counter() - t0) / repeat * 1000.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repeat", type=int, default=20)
    a = ap.parse_args()

    fs_data = float(sampling_rate())
    idx = mafaulda.build_index()
    norm = idx[idx.cls == "normal"]
    row = norm.iloc[len(norm) // 2]
    x_full = mafaulda.load(row.path, channels=["u_radial"])["u_radial"].to_numpy()
    rot = float(mafaulda.speed_hz(row.to_frame().T).iloc[0])

    cases = [
        ("หน้าต่างที่โมเดลใช้  20,972 @ 51,200 Hz", 20_972, fs_data),
        ("หน้าต่างสำหรับ ESP32  8,192 @ 20,000 Hz", 8_192, 20_000.0),
    ]

    print(f"ไฟล์ที่ใช้วัด {Path(row.rel).name}  ความเร็วรอบ {rot:.2f} Hz\n")
    print(f"{'กรณี':42s} {'12 ตัวชี้วัด':>14s} {'FFT':>10s} {'envelope':>11s}")
    last = None
    for label, n, fs in cases:
        x = x_full[:n].astype(float)
        # ต้องส่ง tol_hz ให้ตรงกับความละเอียดของหน้าต่าง มิฉะนั้นหน้าต่าง
        # ค้นพีคจะแคบกว่าหนึ่งช่องความถี่แล้วได้แอมพลิจูด 0
        tol = max(0.02 * rot, 2.0 * fs / n)
        t_all = bench(lambda: channel_features(x, rot, tol_hz=tol, fs=fs), a.repeat)
        t_fft = bench(lambda: spectral.spectrum(x, fs), a.repeat)
        t_env = bench(lambda: spectral.envelope_spectrum(x, fs), a.repeat)
        print(f"{label:42s} {t_all:11.2f} ms {t_fft:7.2f} ms {t_env:8.2f} ms")
        last = t_all

    six = last * N_CHANNELS
    print()
    print(f"ที่หน้าต่าง 8,192 ตัวอย่าง · {N_CHANNELS} ช่อง = {six:.1f} ms")
    print(f"งบเวลาต่อหนึ่งหน้าต่าง (คาบส่ง 10 วินาที) = {PERIOD_MS:,.0f} ms")
    print(f"ใช้ไป {six / PERIOD_MS * 100:.3f}% ของงบ")
    print()
    print("ความเร็วไม่ใช่ข้อจำกัด เพราะอุปกรณ์คำนวณเพียงหนึ่งหน้าต่างทุก 10 วินาที")
    print("ไม่ได้คำนวณต่อเนื่อง จึงมีเวลาว่างราว 9.6 วินาทีระหว่างรอบ")
    print()
    print("หน่วยความจำ ซึ่งเป็นข้อจำกัดที่น่ากังวลกว่า")
    for dtype, nbytes in (("int16", 2), ("float32", 4)):
        kb = 8192 * N_CHANNELS * nbytes / 1024
        print(f"  บัฟเฟอร์ดิบ 8,192 x {N_CHANNELS} ช่อง {dtype:8s} = {kb:6.1f} kB")
    print(f"  บัฟเฟอร์ FFT เชิงซ้อน 8,192 จุด float32  = {8192*2*4/1024:6.1f} kB")
    print()
    print("ESP32 มี SRAM 520 kB แต่สแตก WiFi และระบบปฏิบัติการกินไปส่วนหนึ่ง")
    print("เหลือ heap ใช้ได้จริงราว 250-300 kB -> แบบ float32 ตึงเกินไป")
    print("ทางแก้: เก็บดิบเป็น int16 แล้วแปลงทีละช่อง หรือใช้บอร์ดที่มี PSRAM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

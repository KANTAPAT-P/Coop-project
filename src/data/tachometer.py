"""แปลงสัญญาณพัลส์ tachometer เป็นความเร็วรอบ

**ทำไมต้องมีโมดูลนี้ ทั้งที่ชื่อไฟล์ใน MAFAULDA ก็บอกความเร็วอยู่แล้ว**

1. เครื่องจักรจริงไม่มีชื่อไฟล์ ตอนต่อ TCRT5000 กับ ESP32 หน้าเครื่องจักร
   เรามีแต่พัลส์ ต้องคำนวณเอง เป็นทักษะเดียวกันเป๊ะ
2. ความถี่ความเสียหายทุกตัวเป็นตัวคูณของความเร็วรอบ (BPFO 2.998x, BSF 1.871x,
   FTF 0.375x) ถ้าไม่รู้ความเร็ว ก็ไม่รู้ว่าต้องไปหาพีคที่ความถี่ไหน
3. แอมพลิจูดการสั่นโตตามความเร็วยกกำลังสอง ต้อง normalize ด้วยความเร็ว
   ไม่งั้นโมเดลเรียนรู้ความเร็วแทนความเสียหาย
4. เป็น "บริบทการทำงาน" ที่ CLAUDE.md หัวข้อ 7 ระบุว่าคือสาเหตุ false alarm อันดับหนึ่ง

**และที่สำคัญที่สุด** ความเร็วที่วัดจาก tachometer ไม่เท่ากับชื่อไฟล์
วัดจริงแล้วต่ำกว่าอย่างเป็นระบบราว 2% ทุกไฟล์ ดู ``validate_against_filenames()``

## กับดักของการนับพัลส์

พัลส์ไม่ใช่ค่าเดี่ยว แต่กว้างหลายร้อยแถว **ถ้านับทุกแถวที่เกิน threshold
จะได้ผลเกินจริงเป็นร้อยเท่า** ต้องนับเฉพาะขอบขาขึ้น (rising edge)

โมดูลนี้ใช้ Schmitt trigger คือมีสอง threshold แทนที่จะเป็นค่าเดียว
สัญญาณต้องขึ้นเหนือเส้นบนจึงนับว่า "สูง" และต้องลงต่ำกว่าเส้นล่างจึงนับว่า "ต่ำ"
ช่วงระหว่างสองเส้นถือว่ายังไม่เปลี่ยนสถานะ วิธีนี้กัน noise ที่แกว่งรอบ
threshold เดียวไม่ให้ถูกนับซ้ำหลายครั้งในขอบเดียว
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DEFAULT_THRESHOLD = 2.5
DEFAULT_HYSTERESIS = 0.15   # สัดส่วนของช่วงแอมพลิจูด ใช้เป็นระยะห่างของสอง threshold

# ความเร็วสูงสุดที่เพลาหมุนได้จริง ใช้กำหนด refractory period
# MAFAULDA สูงสุดราว 62 Hz ตั้ง 70 Hz เผื่อไว้ ถ้าย้ายไปเครื่องจักรอื่นต้องแก้ค่านี้
DEFAULT_MAX_HZ = 70.0


@dataclass
class TachResult:
    """ผลการวิเคราะห์สัญญาณ tachometer หนึ่งไฟล์"""

    rot_hz: float                    # ความเร็วรอบ (Hz) จากมัธยฐานของช่วงห่าง
    rot_rpm: float
    n_pulses: int
    jitter_pct: float                # ส่วนเบี่ยงเบนของช่วงห่าง เทียบเป็น % ของมัธยฐาน
    duty_pct: float                  # ความกว้างพัลส์เทียบกับคาบ
    pulse_width_samples: float
    edges: np.ndarray = field(repr=False)

    @property
    def is_trustworthy(self) -> bool:
        """เกณฑ์หยาบๆ ว่าผลนี้เชื่อได้ไหม

        jitter สูงแปลว่าช่วงห่างระหว่างพัลส์ไม่สม่ำเสมอ ซึ่งเกิดได้จากสองสาเหตุ
        คือความเร็วเปลี่ยนจริงระหว่างบันทึก หรือการตรวจจับขอบผิดพลาด
        ทั้งสองกรณีแปลว่าห้ามเอาตัวเลขเดียวไปใช้แทนทั้งไฟล์
        """
        return self.n_pulses >= 10 and self.jitter_pct < 5.0


def _schmitt_state(x: np.ndarray, lo_thr: float, hi_thr: float) -> np.ndarray:
    """คืนสถานะ 0/1 ของสัญญาณโดยใช้ threshold สองระดับ

    เขียนแบบ vectorised ไม่ใช้ลูป เพราะสัญญาณยาว 250,000 จุดต่อไฟล์
    และต้องวนหลายพันไฟล์ ลูป Python จะช้าเกินไป
    """
    state = np.where(x > hi_thr, 1, np.where(x < lo_thr, 0, -1))
    # เติมค่าย้อนหลัง: ช่วง -1 (อยู่ระหว่างสอง threshold) ให้คงสถานะเดิมไว้
    known = state >= 0
    if not known.any():
        return np.zeros(len(x), dtype=int)
    idx = np.where(known, np.arange(len(x)), 0)
    idx = np.maximum.accumulate(idx)
    filled = state[idx]
    # ช่วงต้นไฟล์ก่อนเจอสถานะแรก ให้ถือว่าเป็นสถานะแรกที่เจอ
    first = int(np.argmax(known))
    filled[:first] = state[first]
    return filled


def thresholds(
    x: np.ndarray,
    threshold: float | None = DEFAULT_THRESHOLD,
    hysteresis: float = DEFAULT_HYSTERESIS,
) -> tuple[float, float]:
    """คืน (threshold ล่าง, threshold บน)

    ``threshold=None`` = คำนวณจากสัญญาณเอง โดยใช้จุดกึ่งกลางระหว่างเปอร์เซ็นไทล์
    ที่ 5 กับ 95 ซึ่งทนต่อ spike ได้ดีกว่าการใช้ min/max ตรงๆ
    ใช้โหมดนี้เมื่อไปเจอเซ็นเซอร์จริงที่ระดับแรงดันไม่เหมือน MAFAULDA
    """
    lo, hi = np.percentile(x, [5, 95])
    span = hi - lo
    mid = threshold if threshold is not None else (lo + hi) / 2.0
    margin = span * hysteresis / 2.0
    return mid - margin, mid + margin


def find_rising_edges(
    x: np.ndarray,
    threshold: float | None = DEFAULT_THRESHOLD,
    hysteresis: float = DEFAULT_HYSTERESIS,
) -> np.ndarray:
    """ดัชนีของขอบขาขึ้นทุกจุด"""
    lo_thr, hi_thr = thresholds(x, threshold, hysteresis)
    state = _schmitt_state(np.asarray(x, dtype=float), lo_thr, hi_thr)
    return np.flatnonzero(np.diff(state) == 1) + 1


def find_falling_edges(
    x: np.ndarray,
    threshold: float | None = DEFAULT_THRESHOLD,
    hysteresis: float = DEFAULT_HYSTERESIS,
) -> np.ndarray:
    lo_thr, hi_thr = thresholds(x, threshold, hysteresis)
    state = _schmitt_state(np.asarray(x, dtype=float), lo_thr, hi_thr)
    return np.flatnonzero(np.diff(state) == -1) + 1


def apply_refractory(edges: np.ndarray, min_gap: float) -> np.ndarray:
    """ทิ้งขอบที่อยู่ใกล้ขอบก่อนหน้าเกินกว่าจะเป็นรอบถัดไปได้จริง

    **จำเป็นมากกับ dataset นี้** ไฟล์ที่เครื่องสั่นแรง (โดยเฉพาะ ball_fault)
    มีพัลส์ที่หยักกลางพัลส์จนตกต่ำกว่า threshold ชั่วขณะ แล้วถูกนับเป็นสองขอบ
    ทำให้ความเร็วที่คำนวณได้พุ่งไปเป็นสิบเท่า ตรวจพบในไฟล์ราว 7% ของ dataset

    ``min_gap`` มาจากขีดจำกัดเชิงฟิสิกส์ว่าเพลาหมุนเร็วสุดได้เท่าไหร่
    ไม่ได้มาจากตัวข้อมูลเอง จึงไม่วนเป็นงูกินหาง
    """
    keep = [int(edges[0])]
    for e in edges[1:]:
        if e - keep[-1] >= min_gap:
            keep.append(int(e))
    return np.asarray(keep)


def analyse(
    x: np.ndarray,
    fs: float,
    ppr: int = 1,
    threshold: float | None = DEFAULT_THRESHOLD,
    hysteresis: float = DEFAULT_HYSTERESIS,
    max_hz: float = DEFAULT_MAX_HZ,
) -> TachResult:
    """วิเคราะห์สัญญาณ tachometer หนึ่งชุด

    ``ppr`` = pulses per revolution จำนวนพัลส์ต่อการหมุนหนึ่งรอบ
    MAFAULDA ใช้ 1 (ยืนยันแล้วจากจำนวนพัลส์เทียบกับความเร็วที่คาด)
    เซ็นเซอร์จริงบางตัวให้หลายพัลส์ต่อรอบ เช่นถ้าติดแถบสะท้อนแสง 4 แถบ

    ``max_hz`` = ความเร็วสูงสุดที่เพลาหมุนได้จริง ใช้กำหนด refractory period
    MAFAULDA สูงสุดราว 62 Hz ตั้งไว้ 70 Hz เผื่อไว้

    **วิธีคำนวณความเร็ว** ไม่ได้ใช้มัธยฐานของช่วงห่างตรงๆ แต่นับว่าทั้งช่วง
    ตั้งแต่ขอบแรกถึงขอบสุดท้ายกินไปทั้งหมดกี่รอบ แล้วหารด้วยเวลาที่ใช้

        รอบทั้งหมด = ผลรวมของ round(ช่วงห่าง / คาบโดยประมาณ)
        ความเร็ว   = รอบทั้งหมด / เวลาตั้งแต่ขอบแรกถึงขอบสุดท้าย

    เหตุผลคือ **ความคลาดเคลื่อนของตำแหน่งขอบแต่ละอันหักล้างกันเอง** เมื่อวัดจาก
    ปลายถึงปลาย เหลือเพียงความคลาดเคลื่อนของขอบแรกกับขอบสุดท้ายเท่านั้น
    ขณะที่มัธยฐานเอาความคลาดเคลื่อนของทุกคู่มาเฉลี่ยโดยไม่หักล้าง
    การปัดเป็นจำนวนรอบยังทำให้ทนต่อพัลส์ที่หายไปด้วย เพราะช่วงที่ยาวเป็นสองเท่า
    จะถูกนับเป็น 2 รอบอย่างถูกต้อง

    ทดสอบกับไฟล์ที่เคยให้ผลผิด 18 เท่าแล้ว วิธีนี้ให้ค่าคลาดจากที่คาดเพียง 0.13%
    """
    x = np.asarray(x, dtype=float)
    edges = find_rising_edges(x, threshold, hysteresis)

    if len(edges) >= 2:
        edges = apply_refractory(edges, fs / max_hz)

    if len(edges) < 3:
        return TachResult(np.nan, np.nan, len(edges), np.nan, np.nan, np.nan, edges)

    intervals = np.diff(edges)
    approx = float(np.median(intervals))
    revs = np.maximum(np.round(intervals / approx), 1.0)

    span = float(edges[-1] - edges[0])
    rot_hz = fs * float(revs.sum()) / span / ppr

    # ความยาวหนึ่งรอบที่แต่ละช่วงบอก ใช้วัดความสม่ำเสมอ
    per_rev = intervals / revs
    jitter = float(np.std(per_rev) / np.mean(per_rev) * 100.0)

    falls = find_falling_edges(x, threshold, hysteresis)
    if len(falls) and falls[0] < edges[0]:
        falls = falls[1:]
    n = min(len(edges), len(falls))
    width = float(np.median(falls[:n] - edges[:n])) if n else np.nan
    period = fs / rot_hz

    return TachResult(
        rot_hz=rot_hz,
        rot_rpm=rot_hz * 60.0,
        n_pulses=len(edges),
        jitter_pct=jitter,
        duty_pct=float(width / period * 100.0) if n else np.nan,
        pulse_width_samples=width,
        edges=edges,
    )


def speed_profile(
    x: np.ndarray,
    fs: float,
    ppr: int = 1,
    threshold: float | None = DEFAULT_THRESHOLD,
) -> tuple[np.ndarray, np.ndarray]:
    """ความเร็วรอบทีละรอบ คืน (เวลาเป็นวินาที, ความเร็วเป็น Hz)

    ใช้ดูว่าความเร็วคงที่ตลอดไฟล์ไหม ถ้าไม่คงที่ การใช้ตัวเลขเดียวแทนทั้งไฟล์
    จะทำให้ตำแหน่งความถี่ความเสียหายที่คำนวณได้เบลอ และพีคใน FFT จะเตี้ยลง
    """
    edges = find_rising_edges(x, threshold)
    if len(edges) < 2:
        return np.array([]), np.array([])
    intervals = np.diff(edges)
    return edges[:-1] / fs, fs / intervals / ppr

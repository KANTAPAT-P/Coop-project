"""การวิเคราะห์ในโดเมนความถี่ — FFT ธรรมดา และ envelope analysis

**ทำไมต้องมีสองอย่าง**

FFT ธรรมดาเห็นสิ่งที่สั่นที่ความถี่นั้นตรงๆ ใช้ได้ดีกับ imbalance (พีคที่ 1x
ของความเร็วรอบ) และ misalignment (พีคที่ 2x เด่นผิดปกติ)

แต่กับตลับลูกปืนมันไม่เห็น เพราะรอยแตกเล็กๆ ไม่ได้ทำให้เกิดการสั่นที่ความถี่
BPFO โดยตรง มันแค่ **กระแทก** ทุกครั้งที่ลูกปืนกลิ้งผ่านรอย แล้วแรงกระแทกนั้น
ไปกระตุ้นความถี่ธรรมชาติของโครงสร้างที่ 2-5 kHz ให้สั่นแล้วค่อยๆ ซาลง
สิ่งที่เซ็นเซอร์เห็นจึงเป็นคลื่น 2-5 kHz ที่ถูกมอดูเลตด้วยจังหวะกระแทกช้าๆ
FFT ธรรมดาจะเห็นแค่ก้อนพลังงานแถว 2-5 kHz ไม่เห็นจังหวะที่ซ่อนอยู่

envelope analysis ดึงจังหวะนั้นออกมา 3 ขั้น
    1. bandpass 2-5 kHz  ตัดทุกอย่างทิ้ง เหลือเฉพาะย่านที่ถูกกระตุ้น
    2. Hilbert transform หาเส้นขอบบน (envelope) ของคลื่นที่เหลือ
    3. FFT ของ envelope  จังหวะกระแทกโผล่เป็นพีคที่ BPFO / BSF / FTF
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, hilbert

DEFAULT_BAND = (2000.0, 5000.0)


def spectrum(
    x: np.ndarray, fs: float, detrend: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """สเปกตรัมแอมพลิจูดด้านเดียว หน่วยเดียวกับสัญญาณเข้า

    ใช้หน้าต่าง Hann เพราะสัญญาณ 5 วินาทีไม่ได้จบพอดีรอบ ถ้าตัดดิบๆ
    ปลายสองข้างจะไม่ต่อกัน เกิด spectral leakage ทำให้พีคเตี้ยลงและ
    มีหางฟุ้งออกข้างๆ จนอ่านค่าผิด
    """
    x = np.asarray(x, dtype=float)
    if detrend:
        x = x - x.mean()

    w = np.hanning(len(x))
    # ชดเชยพลังงานที่หน้าต่างกินไป ไม่งั้นแอมพลิจูดจะต่ำกว่าความจริงราวครึ่งหนึ่ง
    gain = w.mean()

    mag = np.abs(np.fft.rfft(x * w)) * 2.0 / (len(x) * gain)
    return np.fft.rfftfreq(len(x), 1.0 / fs), mag


def bandpass(
    x: np.ndarray, fs: float, lo: float, hi: float, order: int = 4
) -> np.ndarray:
    """กรองผ่านย่าน ใช้ filtfilt เพื่อไม่ให้สัญญาณเลื่อนเฟส

    filtfilt กรองไปกลับสองรอบ ผลคือ zero phase shift ซึ่งจำเป็นเวลา
    ต้องดูจังหวะเวลาของการกระแทก ถ้าใช้ lfilter ธรรมดาสัญญาณจะเลื่อน
    """
    nyq = fs / 2.0
    if not 0 < lo < hi < nyq:
        raise ValueError(f"ย่านความถี่ต้องอยู่ใน (0, {nyq}) แต่ได้ ({lo}, {hi})")
    b, a = butter(order, [lo / nyq, hi / nyq], btype="band")
    return filtfilt(b, a, x)


def envelope(x: np.ndarray, fs: float, band: tuple[float, float] = DEFAULT_BAND) -> np.ndarray:
    """เส้นขอบของสัญญาณหลังกรองผ่านย่านที่กำหนด"""
    return np.abs(hilbert(bandpass(np.asarray(x, dtype=float), fs, *band)))


def envelope_spectrum(
    x: np.ndarray, fs: float, band: tuple[float, float] = DEFAULT_BAND
) -> tuple[np.ndarray, np.ndarray]:
    """สเปกตรัมของ envelope — เครื่องมือหลักในการหาความเสียหายตลับลูกปืน"""
    env = envelope(x, fs, band)
    return spectrum(env, fs, detrend=True)


def fault_frequencies(rot_hz: float, coefficients: dict[str, float]) -> dict[str, float]:
    """แปลงตัวคูณเป็นความถี่จริงเป็น Hz

    MAFAULDA ไม่มีข้อมูล inner race ตัวคูณ BPFI จึงมีไว้เผื่อ dataset อื่น
    ผู้เรียกควรเลือกเฉพาะตัวที่เกี่ยวข้องไปแสดงผล

    ⚠️ **BPFO ของตลับลูกปืนตัวนี้แยกจากฮาร์มอนิกที่ 3 ของความเร็วรอบไม่ได้**
    ตัวคูณคือ 2.9980 ซึ่งห่างจาก 3.0000 อยู่แค่ 0.002 ที่ความเร็ว 30 Hz
    แปลว่าห่างกัน 0.06 Hz แต่ไฟล์ยาว 5 วินาทีให้ความละเอียดความถี่แค่
    1/5 = 0.2 Hz ซึ่งหยาบกว่าระยะห่างถึง 3 เท่า สองพีคนี้จึงตกลงในช่องเดียวกัน
    เสมอ ไม่ว่าจะซูมแค่ไหนก็แยกไม่ออก ดูฟังก์ชัน ``resolution_warning``
    """
    return {name: rot_hz * k for name, k in coefficients.items()}


def resolution_warning(
    rot_hz: float, coefficients: dict[str, float], duration_s: float, tol_bins: float = 1.0
) -> dict[str, str]:
    """บอกว่าความถี่ความเสียหายตัวไหนแยกจากฮาร์มอนิกของความเร็วรอบไม่ได้

    ใช้ตรวจก่อนจะสรุปว่า "เจอพีคที่ BPFO แปลว่ามีความเสียหายที่รางนอก"
    ถ้าพีคนั้นอยู่ห่างจาก n เท่าของความเร็วรอบน้อยกว่าความละเอียดของ FFT
    ข้อสรุปนั้นไม่มีน้ำหนัก เพราะเครื่องจักรปกติก็มีฮาร์มอนิกของความเร็วรอบอยู่แล้ว
    """
    df_res = 1.0 / duration_s
    out = {}
    for name, k in coefficients.items():
        nearest = round(k)
        if nearest == 0:
            continue
        gap_hz = abs(k - nearest) * rot_hz
        if gap_hz < df_res * tol_bins:
            out[name] = (
                f"{name} ({k:.4f}x) ห่างจาก {nearest}x ของความเร็วรอบเพียง {gap_hz:.3f} Hz "
                f"ขณะที่ความละเอียด FFT คือ {df_res:.3f} Hz — แยกไม่ออก"
            )
    return out


def band_energy(freqs: np.ndarray, mag: np.ndarray, lo: float, hi: float) -> float:
    """พลังงานรวมในช่วงความถี่หนึ่ง ใช้เป็น feature ที่ ESP32 คำนวณเองได้"""
    m = (freqs >= lo) & (freqs <= hi)
    return float(np.sqrt(np.sum(np.square(mag[m]))))


def peak_near(
    freqs: np.ndarray, mag: np.ndarray, target: float, tol_frac: float = 0.03
) -> tuple[float, float]:
    """หาพีคสูงสุดในหน้าต่างรอบความถี่เป้าหมาย คืน (ความถี่ที่เจอ, แอมพลิจูด)

    ต้องมีหน้าต่างเผื่อ เพราะความเร็วรอบจริงแกว่งเล็กน้อยระหว่างบันทึก
    และตัวคูณ BPFO/BSF/FTF เองก็เป็นค่าประมาณที่คิดจากเรขาคณิตอุดมคติ
    โดยสมมติว่าลูกปืนกลิ้งโดยไม่ลื่นเลย ซึ่งจริงๆ มีการลื่นเสมอ
    """
    lo, hi = target * (1 - tol_frac), target * (1 + tol_frac)
    m = (freqs >= lo) & (freqs <= hi)
    if not m.any():
        return target, 0.0
    i = np.argmax(mag[m])
    return float(freqs[m][i]), float(mag[m][i])

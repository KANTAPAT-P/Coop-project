"""feature ในโดเมนเวลา — ตัวพื้นฐานที่สุดของงาน condition monitoring

ทั้งสี่ตัวนี้คำนวณเร็วมาก เบาพอที่จะรันบน ESP32 ได้ตรงๆ จึงเป็นชุดที่ตั้งใจ
จะใช้จริงตอน Checkpoint 4 ไม่ใช่แค่ของเล่นตอนสำรวจข้อมูล

**ตัวไหนบอกอะไร**

- ``rms``           พลังงานรวมของการสั่น ไวต่อ imbalance และ misalignment
                    แต่ไม่ไวต่อความเสียหายเฉพาะจุดในระยะเริ่มต้น
- ``peak``          ค่าสูงสุด ไวต่อการกระแทกครั้งเดียว แต่ก็ไวต่อสัญญาณรบกวนด้วย
- ``crest_factor``  peak / rms — บอกว่าสัญญาณ "แหลม" แค่ไหน
                    ตลับลูกปืนที่เริ่มมีรอยแตกจะกระแทกเป็นจังหวะ ทำให้ peak ขึ้น
                    ขณะที่ rms ยังไม่ขึ้น ค่านี้จึงขึ้นก่อน rms
- ``kurtosis``      ความ "หางหนา" ของการกระจาย สัญญาณสุ่มปกติได้ 3
                    ยิ่งมีการกระแทกเป็นพัลส์แหลมมาก ค่ายิ่งสูงกว่า 3

**กับดักของ crest factor และ kurtosis** พอความเสียหายลุกลามจนกระแทกถี่มาก
สัญญาณจะกลับไปดูเหมือน random noise อีกครั้ง ทั้งสองค่าจะ**ตกกลับลงมา**
ทั้งที่ของจริงแย่ลง จึงห้ามใช้ตัวเดียวโดดๆ ต้องดูคู่กับ rms ที่เพิ่มขึ้นเรื่อยๆ
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

FEATURE_NAMES = ["rms", "peak", "crest_factor", "kurtosis"]


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def peak(x: np.ndarray) -> float:
    """ใช้ค่าสัมบูรณ์สูงสุดเทียบกับค่าเฉลี่ย เพื่อไม่ให้ DC offset มามีผล"""
    return float(np.max(np.abs(x - np.mean(x))))


def crest_factor(x: np.ndarray) -> float:
    r = rms(x - np.mean(x))
    return float(peak(x) / r) if r > 0 else np.nan


def kurtosis(x: np.ndarray) -> float:
    """fisher=False ให้ค่า 3 สำหรับการแจกแจงปกติ ตามที่ใช้กันในงานสั่นสะเทือน"""
    return float(stats.kurtosis(x, fisher=False))


def compute(x: np.ndarray) -> dict[str, float]:
    """คำนวณทั้งสี่ตัวในครั้งเดียว"""
    return {
        "rms": rms(x),
        "peak": peak(x),
        "crest_factor": crest_factor(x),
        "kurtosis": kurtosis(x),
    }


def compute_frame(df: pd.DataFrame) -> pd.DataFrame:
    """คำนวณ feature ให้ทุกคอลัมน์ของ DataFrame คืนตาราง feature x channel"""
    return pd.DataFrame({c: compute(df[c].to_numpy()) for c in df.columns})

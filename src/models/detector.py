"""ตัวตรวจจับความผิดปกติชั้นที่ 1 — เทรนจากข้อมูลปกติเท่านั้น

## ทำไมต้องเทรนจากข้อมูลปกติเท่านั้น

ที่หน้างานจริงเราจะไม่มีตัวอย่างของความเสียหาย เพราะไม่มีใครยอมให้เครื่องจักร
เสียเพื่อเก็บข้อมูล สิ่งที่เก็บได้คือ "ตอนนี้เครื่องทำงานปกติ" เท่านั้น
ตัวตรวจจับชั้นที่ 1 จึงต้องเรียนรู้ว่า**ปกติหน้าตาเป็นอย่างไร** แล้วเตือนเมื่อหลุดออกไป
ไม่ใช่เรียนรู้ว่าความเสียหายหน้าตาเป็นอย่างไร

การประเมินในไฟล์นี้จึงเทรนด้วยคลาส `normal` ของ MAFAULDA อย่างเดียว
แล้วเอาคลาสที่เสียทั้งห้าคลาสมาวัดว่าจับได้แค่ไหน **โดยที่โมเดลไม่เคยเห็นมันเลย**

## 🚨 ปัญหาที่ต้องแก้ก่อนอย่างอื่น: ตัวชี้วัดเปลี่ยนตามความเร็วรอบ

วัดในคลาส `normal` เอง (ไม่มีความเสียหายใดๆ) พบว่า **34 จาก 72 ตัวชี้วัด
มีสหสัมพันธ์กับความเร็วรอบเกิน 0.7** และ 48 ตัวเกิน 0.5 ตัวที่แรงที่สุดคือ
`u_axial.e_mid` ที่ 0.98

**ถ้าตั้งเกณฑ์เป็นค่าคงที่ตัวเดียว ระบบจะเตือนทุกครั้งที่เครื่องเร่งรอบ**
ซึ่งเป็นพฤติกรรมปกติ ไม่ใช่ความเสียหาย และจะถูกคนหน้างานปิดทิ้งภายในสัปดาห์เดียว

**วิธีแก้ที่ใช้** ประมาณเส้นฐานของแต่ละตัวชี้วัด**เป็นฟังก์ชันของความเร็วรอบ**
แล้ววัดว่าค่าที่อ่านได้ห่างจากเส้นฐาน ณ ความเร็วนั้นกี่เท่าของการกระจายตัว

    ค่าที่คาด = a + b x rot_hz              (ประมาณจากข้อมูลปกติ)
    z         = (ค่าที่วัด - ค่าที่คาด) / การกระจายตัวของเศษเหลือ

⚠️ นี่เป็นวิธีแก้ชั้นต้น **ไม่ใช่วิธีมาตรฐานของวงการ** วิธีมาตรฐานคือ
**order tracking** คือสุ่มสัญญาณใหม่ตามมุมเพลาแทนตามเวลา ซึ่งทำให้ความถี่
ความเสียหายอยู่ตำแหน่งเดิมไม่ว่าความเร็วจะเปลี่ยน
(Sanami & Aghdam, ACC 2026 — ดู `paper/literature-review.md` ฉบับ 08)
ควรทำเป็นขั้นถัดไป ส่วนไฟล์นี้แก้ด้วยการ normalize ซึ่งพอใช้ได้แต่ไม่เท่า

## ทำไมใช้ log กับตัวชี้วัดที่เป็นบวกล้วน

ตัวชี้วัดอย่าง `rms`, `p2p`, `e_low` เป็นปริมาณเชิงสเกล การสั่นแรงขึ้นสองเท่า
ทำให้ค่าพวกนี้ขึ้นสองเท่า ไม่ใช่บวกค่าคงที่ การกระจายตัวจึงกว้างขึ้นตามค่ากลาง
(heteroscedastic) ถ้าหาเศษเหลือบนสเกลดิบ ที่ความเร็วสูงจะกระจายกว้างกว่าที่
ความเร็วต่ำหลายเท่า แล้ว z ตัวเดียวจะคุมทั้งช่วงไม่ได้

การใส่ log เปลี่ยนความสัมพันธ์แบบคูณให้เป็นแบบบวก ทำให้การกระจายตัวสม่ำเสมอขึ้น
และทำให้ z ตีความได้ว่า "สูงกว่าที่คาดกี่เปอร์เซ็นต์" แทน "สูงกว่ากี่หน่วย"

ส่วน `kurt`, `crest`, `r21` ไม่ใส่ log เพราะเป็นอัตราส่วนหรือรูปร่างอยู่แล้ว
(และ `kurt` ติดลบได้ในทางทฤษฎี)

## 🚨 บทเรียน: MAD เป็นตัวประมาณการกระจายตัวที่ **ผิด** สำหรับงานนี้

รอบแรกใช้ MAD (median absolute deviation) ประมาณการกระจายตัวของเศษเหลือ
เพราะเป็นวิธี "ทนค่าผิดปกติ" ซึ่งเป็นสิ่งที่ดีโดยทั่วไป **แต่ผิดในบริบทนี้**

ผลที่ได้คือ **เตือนผิด 3,360 ครั้งต่อวัน และเตือนผิดบนไฟล์ที่ใช้เทรนเองถึง 6 จาก 29 ไฟล์**
ซึ่งเป็นไปไม่ได้ถ้าเส้นฐานอธิบายข้อมูลของตัวเองได้

เหตุผลที่ MAD ผิด **ข้อมูลที่ใช้เทรนเป็นข้อมูลปกติทั้งหมดโดยการออกแบบ
จึงไม่มี "ค่าผิดปกติ" ให้ต้องทน** ทุกจุดคือตัวอย่างที่ถูกต้องของพฤติกรรมปกติ
รวมถึงจุดที่อยู่หางของการแจกแจง MAD วัดเฉพาะความกว้างของ**ตรงกลาง**
แล้วทิ้งหางไป ซึ่งคือข้อมูลชิ้นเดียวที่เราต้องใช้ตั้งเกณฑ์

วัดจริงพบว่าตัวชี้วัด 6 ตัวมีส่วนเบี่ยงเบนมาตรฐานของเศษเหลือ **สูงกว่าค่าจาก MAD
ถึง 2.1-2.7 เท่า** นำโดย `o_axial.r21` และ `u_axial.r21` ซึ่งสมเหตุสมผล
เพราะ `r21` เป็นอัตราส่วน 2x/1x ที่ระเบิดได้เมื่อพีค 1x เล็ก การแจกแจงจึงมีหางหนัก
โดยธรรมชาติ ไม่ใช่เพราะข้อมูลเสีย

> **บทเรียนที่ใช้ได้ทั่วไป: "ทนค่าผิดปกติ" เป็นคุณสมบัติที่ดีเฉพาะเมื่อมีค่าผิดปกติ
> ถ้าข้อมูลสะอาดโดยการออกแบบ การทนค่าผิดปกติกลายเป็นการทิ้งข้อมูลที่ต้องใช้**

จึงเปลี่ยนมาใช้ส่วนเบี่ยงเบนมาตรฐานของเศษเหลือตรงๆ

## 🚨 บทเรียน: เกณฑ์ที่คำนวณจากสมมติฐานการแจกแจงปกติใช้ไม่ได้

เกณฑ์ z = 4.797 ที่คำนวณจากสมมติฐานการแจกแจงปกติบวก Bonferroni **ให้ผลที่แย่มาก**
เพราะเศษเหลือจริงมีหางหนักกว่าการแจกแจงปกติ

และไฟล์ที่หลุดเกณฑ์ **กระจุกอยู่ที่ปลายทั้งสองข้างของช่วงความเร็ว**
(อันดับ 0, 27, 28 จาก 29 ไฟล์) ซึ่งเป็นลายเซ็นของการใช้**เส้นตรงกับความสัมพันธ์ที่โค้ง**
เศษเหลือที่ปลายจึงใหญ่อย่างเป็นระบบ บวกกับจุดปลายมี leverage สูงที่ดึงเส้นเอง

**วิธีแก้: ตั้งเกณฑ์จากข้อมูลด้วย leave-one-out ไม่ใช่จากสูตร**
ตัดไฟล์ปกติออกหนึ่งไฟล์ ประมาณเส้นฐานใหม่จากที่เหลือ แล้วให้คะแนนไฟล์ที่ตัดออก
ทำซ้ำทุกไฟล์ จะได้การแจกแจงของคะแนนบนข้อมูลที่โมเดล**ไม่เคยเห็น**
แล้วตั้งเกณฑ์จากการแจกแจงนั้น ไม่ต้องสมมติรูปร่างใดๆ

## สองกฎการตัดสิน: `max_z` กับ `vote`

**`max_z`** เตือนเมื่อตัวชี้วัดตัวใดตัวหนึ่งหลุดเกณฑ์
ไวที่สุดและอธิบายได้ดีที่สุด **แต่เปราะ** เพราะเป็นสถิติค่าสูงสุดจาก 72 ตัว
ถ้าตัวใดตัวหนึ่งมีหางหนักเป็นพิเศษ มันจะจุดเตือนเองตลอด

**`vote`** เตือนเมื่อ**จำนวนตัวชี้วัดที่หลุดเกณฑ์ย่อย**มากกว่าที่กำหนด
ทนกว่ามาก เพราะตัวชี้วัดเดียวที่แกว่งไม่พอทำให้เตือน และสอดคล้องกับฟิสิกส์
ความเสียหายจริงกระทบหลายช่องและหลายตัวชี้วัดพร้อมกัน ขณะที่สัญญาณรบกวน
กระทบตัวเดียว

เลือกกฎไหนตัดสินด้วยการวัด ไม่ใช่ด้วยความชอบ ดู `src/models/eval_detector.py`

## ทำไมไม่ใช้ Mahalanobis distance

แผนเดิมใน `CLAUDE.md` คือไล่จากเกณฑ์สถิติ -> Mahalanobis -> Isolation Forest
**แต่ Mahalanobis ใช้ไม่ได้กับข้อมูลชุดนี้** เพราะต้องประมาณเมทริกซ์ความแปรปรวนร่วม
ขนาด 72x72 จากไฟล์ปกติเพียง 49 ไฟล์ เมทริกซ์จะเป็น singular (อันดับไม่เต็ม)
ทางแก้คือลดมิติหรือใส่ regularization ซึ่งเพิ่มพารามิเตอร์ที่ต้องปรับโดยไม่มี
ข้อมูลให้ปรับ **จึงข้ามขั้นนี้ไปอย่างมีเหตุผล ไม่ใช่เพราะลืม**

`max |z|` มีข้อดีที่สำคัญกว่าในบริบทนี้คือ **บอกได้ว่าตัวชี้วัดตัวไหนทำให้เตือน**
ซึ่งต่อกับตารางลายเซ็นใน `CLAUDE.md` หัวข้อ 5 ได้ตรงๆ และเป็นสิ่งที่ช่างซ่อม
ต้องการจริง ระบบที่บอกได้แค่ "คะแนนความผิดปกติ 0.87" ไม่มีใครใช้

## เกณฑ์มาจากไหน

ตั้งจาก**ข้อมูลปกติเท่านั้น ห้ามดูข้อมูลที่เสีย** ไม่งั้นคือการรั่วของข้อมูล

ถ้าเศษเหลือกระจายแบบปกติ และเราดู `n_feat` ตัวชี้วัดพร้อมกัน โอกาสที่
**อย่างน้อยหนึ่งตัว**หลุดเกณฑ์โดยที่เครื่องปกติดี คือ

    p(เตือนผิด ต่อข้อความ) = n_feat x p(ตัวเดียวหลุด)     [Bonferroni]

กลับทางได้เป็น ถ้าต้องการเตือนผิดไม่เกิน `k` ครั้งต่อวัน ที่คาบส่ง 10 วินาที
(= 8,640 ข้อความต่อวัน) ต้องใช้

    p(ตัวเดียวหลุด) = k / (8640 x n_feat)
    z* = ค่า z ที่ให้ความน่าจะเป็นสองหางเท่ากับนั้น

⚠️ สมมติฐานว่าหางของการแจกแจงเป็นแบบปกติ **ตรวจไม่ได้จาก 49 ไฟล์**
ตัวเลขที่เชื่อถือได้คืออัตราการเตือนผิดที่**วัดจากไฟล์ปกติที่กันไว้** ไม่ใช่ที่คำนวณ

## เก็บโมเดลเป็น JSON ไม่ใช่ pickle

เพราะต้องส่งไปรันบน Raspberry Pi และต้องเปิดอ่านด้วยตาได้เพื่อตรวจว่าเกณฑ์
สมเหตุสมผล `pickle` ผูกกับเวอร์ชันของไลบรารีและอ่านด้วยตาไม่ได้
ส่วนโมเดลนี้มีแค่สัมประสิทธิ์เส้นตรงกับค่าการกระจายตัว JSON จึงพอ
และทำให้ `ingest.py` ไม่ต้องพึ่ง scikit-learn เลย
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ค่าคงที่ของการแปลง MAD ให้เทียบเท่าส่วนเบี่ยงเบนมาตรฐานของการแจกแจงปกติ
MAD_TO_SIGMA = 1.4826

# ตัวชี้วัดที่เป็นอัตราส่วนหรือรูปร่าง ไม่ใส่ log
NO_LOG = ("kurt", "kurt_band", "crest", "r21", "h1_frac", "env_rel")

# ตัวชี้วัดที่ใช้ได้เฉพาะเมื่อ tachometer เชื่อถือได้
# ตรงกับ schema.usable_for_speed_features
SPEED_DEPENDENT = ("h1_frac", "r21")

# คาบการส่งที่ออกแบบไว้ใน docs/data-pipeline-design.md §5.2
MESSAGES_PER_DAY = 24 * 60 * 60 // 10


def _needs_log(name: str) -> bool:
    return name.rsplit(".", 1)[-1] not in NO_LOG


def is_speed_dependent(name: str) -> bool:
    """ตัวชี้วัดนี้ต้องมี tachometer ที่เชื่อถือได้หรือไม่"""
    return name.rsplit(".", 1)[-1] in SPEED_DEPENDENT


def z_for_alarms_per_day(k: float, n_feat: int,
                         messages_per_day: int = MESSAGES_PER_DAY) -> float:
    """เกณฑ์ z ที่ให้การเตือนผิดไม่เกิน k ครั้งต่อวัน ภายใต้สมมติฐานการแจกแจงปกติ

    ใช้ Bonferroni เพราะเราดูหลายตัวชี้วัดพร้อมกัน ถ้าไม่ปรับ อัตราการเตือนผิด
    จะสูงกว่าที่ตั้งใจเท่ากับจำนวนตัวชี้วัด
    """
    if k <= 0:
        raise ValueError("k ต้องมากกว่า 0")
    p_each = k / (messages_per_day * n_feat)
    p_each = min(p_each, 0.5)
    # ผกผันของการแจกแจงปกติสองหาง ใช้สูตรประมาณเพื่อไม่ต้องพึ่ง scipy
    return float(_norm_isf(p_each / 2.0))


def _norm_isf(p: float) -> float:
    """ผกผันของ survival function ของการแจกแจงปกติมาตรฐาน

    ใช้สูตรประมาณของ Acklam ซึ่งคลาดไม่เกิน 1.15e-9 ในช่วงที่ใช้งาน
    เขียนเองเพื่อให้ `ingest.py` ไม่ต้องพึ่ง scipy ซึ่งหนักสำหรับ Pi
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p ต้องอยู่ระหว่าง 0 ถึง 1")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    q = 1.0 - p                    # แปลง survival เป็น cumulative
    if q < 0.02425:
        r = math.sqrt(-2.0 * math.log(q))
        x = (((((c[0] * r + c[1]) * r + c[2]) * r + c[3]) * r + c[4]) * r + c[5]) / \
            ((((d[0] * r + d[1]) * r + d[2]) * r + d[3]) * r + 1.0)
    elif q <= 0.97575:
        r = q - 0.5
        s = r * r
        x = (((((a[0] * s + a[1]) * s + a[2]) * s + a[3]) * s + a[4]) * s + a[5]) * r / \
            (((((b[0] * s + b[1]) * s + b[2]) * s + b[3]) * s + b[4]) * s + 1.0)
    else:
        r = math.sqrt(-2.0 * math.log(1.0 - q))
        x = -(((((c[0] * r + c[1]) * r + c[2]) * r + c[3]) * r + c[4]) * r + c[5]) / \
            ((((d[0] * r + d[1]) * r + d[2]) * r + d[3]) * r + 1.0)
    return x


@dataclass
class Baseline:
    """เส้นฐานของเครื่องจักรขณะปกติ แยกตามความเร็วรอบ

    ``slope`` และ ``intercept`` คือเส้นตรงของแต่ละตัวชี้วัดเทียบกับ ``rot_hz``
    ``scale`` คือส่วนเบี่ยงเบนมาตรฐานของเศษเหลือ — **ไม่ใช่ MAD** ดูเหตุผลที่หัวไฟล์

    กฎการตัดสินมีสองแบบ เลือกด้วย ``rule``

    * ``"max_z"`` — เตือนเมื่อ ``max |z| > max_z_cut``
    * ``"vote"``  — เตือนเมื่อจำนวนตัวชี้วัดที่ ``|z| > z_feat`` มีไม่น้อยกว่า ``vote_min``
    """

    features: list[str]
    slope: list[float]
    intercept: list[float]
    scale: list[float]
    use_log: list[bool]
    speed_lo: float
    speed_hi: float
    n_train: int
    rule: str = "vote"
    max_z_cut: float = 6.0
    z_feat: float = 3.0
    vote_min: int = 3
    # เกณฑ์เตือนทันทีโดยไม่ต้องรอด่านยืนยันซ้ำ
    #
    # 🚨 **ต้องตั้งจากข้อมูล ไม่ใช่เดา** รอบแรกตั้งไว้ที่ 12.0 ซึ่ง**ผิด**
    # เพราะ max |z| ของไฟล์ปกติเองใน leave-one-out สูงถึง 12.52
    # ไฟล์ปกติจึงข้ามด่านยืนยันซ้ำได้ ทำลายการรับประกันอัตราการเตือนผิดทั้งหมด
    #
    # ``None`` = ปิดช่องทางเตือนทันที ทุกการเตือนต้องผ่านด่าน
    hard_z: float | None = None
    # หน้าต่างที่ใช้เทรน ``{"fs": ..., "n": ...}``
    #
    # 🚨 **ต้องเก็บไว้ ไม่ใช่จำเอาเอง** ค่าของตัวชี้วัดขึ้นกับความยาวหน้าต่าง
    # `env_floor` กับ `env_rel` วัด "พื้น" ของสเปกตรัมซึ่งสูงขึ้นตาม 1/sqrt(N)
    # วัดแล้วว่าหน้าต่างสั้นลง 11.9 เท่าทำให้ค่าพุ่ง 272% และทำให้เครื่องปกติ
    # ติดเกณฑ์พอดี 11 ตัว = เตือนทุกข้อความ
    # ดู ``experiments/2026-10-09-window-length-mismatch.md``
    #
    # ``None`` = โมเดลเก่าที่ไม่ได้บันทึกไว้ จะข้ามการตรวจ (ดู ``window_matches``)
    window: dict | None = None
    meta: dict = field(default_factory=dict)

    # ``threshold`` เก็บไว้เพื่อให้โค้ดเดิมที่อ้างถึงยังทำงาน
    # ค่าที่คืนขึ้นกับกฎที่ใช้ เพราะสองกฎวัดคนละอย่าง
    @property
    def threshold(self) -> float:
        return self.max_z_cut if self.rule == "max_z" else float(self.vote_min)

    def decide(self, max_z: float, n_exceed: int) -> bool:
        """ตัดสินว่าเตือนหรือไม่ ตามกฎที่ตั้งไว้"""
        if self.rule == "max_z":
            return max_z > self.max_z_cut
        return n_exceed >= self.vote_min

    # --------------------------------------------- ตรวจหน้าต่างให้ตรงกับที่เทรน

    # ยอมให้ความยาวคลาดได้เท่านี้ เผื่อการปัดเศษของจำนวนตัวอย่าง
    WINDOW_TOL = 0.02

    def window_matches(self, w: dict | None) -> tuple[bool, str]:
        """หน้าต่างของข้อความตรงกับที่เทรนไหม คืน (ตรงไหม, เหตุผล)

        **ทำไมต้องตรวจ** ฟิลด์ ``window`` อยู่ใน schema ของข้อความมาตั้งแต่
        เวอร์ชันแรกเพื่อป้องกันเรื่องนี้พอดี **แต่ไม่มีใครอ่านมัน จึงป้องกัน
        อะไรไม่ได้เลย** ฟิลด์ที่ไม่มีใครตรวจก็เหมือนไม่มี

        ตรวจสองอย่าง

        1. **ความยาว** ``n/fs`` ต้องคลาดไม่เกิน 2% เพราะคุมความละเอียดความถี่
           และระดับพื้นของสเปกตรัม
        2. **fs** ต้องเท่ากันพอดี เพราะคุมแกนความถี่ และ ``e_high`` นับพลังงาน
           ถึง 10 kHz ซึ่งอยู่ที่ Nyquist พอดีเมื่อ fs = 20 kHz แล้วการ roll-off
           ของฟิลเตอร์กันสัญญาณซ้อนจะกินย่านนั้นไปไม่เท่ากัน
        """
        if self.window is None:
            return True, "โมเดลไม่ได้บันทึกหน้าต่างที่เทรน จึงตรวจไม่ได้"
        if not isinstance(w, dict):
            return False, "ข้อความไม่มีฟิลด์ window"
        try:
            fs, n = float(w["fs"]), float(w["n"])
        except (KeyError, TypeError, ValueError):
            return False, "ฟิลด์ window อ่านค่า fs หรือ n ไม่ได้"
        if fs <= 0 or n <= 0:
            return False, f"window ไม่สมเหตุสมผล fs={fs} n={n}"

        fs0, n0 = float(self.window["fs"]), float(self.window["n"])
        if abs(fs - fs0) > 1e-6:
            return False, (f"fs ไม่ตรงกับที่เทรน ได้ {fs:,.0f} Hz "
                           f"แต่เทรนด้วย {fs0:,.0f} Hz")
        got, want = n / fs, n0 / fs0
        if abs(got - want) > self.WINDOW_TOL * want:
            return False, (f"ความยาวหน้าต่างไม่ตรงกับที่เทรน "
                           f"ได้ {got * 1000:,.0f} ms แต่เทรนด้วย {want * 1000:,.0f} ms")
        return True, ""

    # ---------------------------------------------------------- ประเมิน

    def score_array(self, x: np.ndarray, rot_hz: np.ndarray) -> np.ndarray:
        """คืนเมทริกซ์ z ขนาด (n_sample, n_feature)

        ``x`` ต้องเรียงคอลัมน์ตาม ``self.features``
        """
        x = np.asarray(x, dtype=float)
        rot = np.asarray(rot_hz, dtype=float).reshape(-1, 1)
        use_log = np.asarray(self.use_log)
        t = x.copy()
        # ค่าที่เป็นศูนย์หรือติดลบในช่องที่ควรเป็นบวก ถือว่าเป็นค่าที่วัดไม่ได้
        with np.errstate(divide="ignore", invalid="ignore"):
            t[:, use_log] = np.log(np.where(x[:, use_log] > 0, x[:, use_log], np.nan))
        expected = np.asarray(self.intercept) + np.asarray(self.slope) * rot
        return (t - expected) / np.asarray(self.scale)

    def score(self, feats: dict, rot_hz: float,
              allow_speed_features: bool = True) -> dict:
        """ประเมินหนึ่งข้อความ คืนคะแนนและตัวชี้วัดที่ผิดปกติที่สุด

        ``feats`` เป็น dict ชื่อตัวชี้วัด -> ค่า ตัวที่ไม่มีในข้อความจะถูกข้าม
        ไม่ใช่ถือว่าเป็นศูนย์ เพราะอุปกรณ์แต่ละตัวอาจส่งไม่ครบทุกช่อง

        ``allow_speed_features=False`` เมื่อ tachometer ไม่น่าเชื่อถือ
        จะตัด h1_frac และ r21 ออกจากการตัดสิน
        """
        used, zs = [], []
        for i, name in enumerate(self.features):
            if name not in feats:
                continue
            if not allow_speed_features and is_speed_dependent(name):
                continue
            v = feats[name]
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            if not math.isfinite(v):
                continue
            if self.use_log[i]:
                if v <= 0:
                    continue
                t = math.log(v)
            else:
                t = float(v)
            expected = self.intercept[i] + self.slope[i] * rot_hz
            zs.append((t - expected) / self.scale[i])
            used.append(name)

        if not used:
            return {"score": 0.0, "worst": None, "worst_z": 0.0,
                    "n_used": 0, "n_exceed": 0, "exceeded": [],
                    "in_speed_range": self.in_speed_range(rot_hz)}

        az = np.abs(zs)
        order = np.argsort(az)[::-1]
        exceeded = [{"feature": used[i], "z": round(float(zs[i]), 2)}
                    for i in order if az[i] > self.z_feat]
        j = int(order[0])
        max_z = float(az[j])
        return {
            "score": round(max_z, 3),
            "worst": used[j],
            "worst_z": round(float(zs[j]), 2),
            "n_used": len(used),
            "n_exceed": len(exceeded),
            "exceeded": exceeded[:5],
            "anomaly": self.decide(max_z, len(exceeded)),
            "in_speed_range": self.in_speed_range(rot_hz),
        }

    def in_speed_range(self, rot_hz: float) -> bool:
        """ความเร็วนี้อยู่ในช่วงที่เส้นฐานครอบคลุมหรือไม่

        **สำคัญ** เส้นฐานเป็นเส้นตรงที่ประมาณจากช่วงความเร็วที่เคยเห็น
        ถ้าเครื่องหมุนเร็วหรือช้ากว่าที่เคยเก็บข้อมูลไว้ การคาดการณ์คือการ
        extrapolate ซึ่งเชื่อถือไม่ได้ ต้องบอกผู้ใช้ ไม่ใช่เตือนว่าเสีย
        """
        return self.speed_lo <= rot_hz <= self.speed_hi

    # ------------------------------------------------------- บันทึก/อ่าน

    def to_json(self) -> str:
        d = {
            "kind": "speed-normalised-z",
            "version": 3,          # 3 = เพิ่มฟิลด์ window
            "features": self.features,
            "slope": self.slope,
            "intercept": self.intercept,
            "scale": self.scale,
            "use_log": self.use_log,
            "rule": self.rule,
            "max_z_cut": self.max_z_cut,
            "z_feat": self.z_feat,
            "vote_min": self.vote_min,
            "hard_z": self.hard_z,
            "speed_lo": self.speed_lo,
            "speed_hi": self.speed_hi,
            "n_train": self.n_train,
            "window": self.window,
            "meta": self.meta,
        }
        return json.dumps(d, indent=2, ensure_ascii=False)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Baseline":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        if d.get("kind") != "speed-normalised-z":
            raise ValueError(f"ชนิดโมเดลไม่ตรง: {d.get('kind')!r}")
        return cls(
            features=d["features"], slope=d["slope"], intercept=d["intercept"],
            scale=d["scale"], use_log=d["use_log"],
            rule=d.get("rule", "vote"), max_z_cut=d.get("max_z_cut", 6.0),
            z_feat=d.get("z_feat", 3.0), vote_min=d.get("vote_min", 3),
            hard_z=d.get("hard_z"),
            speed_lo=d["speed_lo"], speed_hi=d["speed_hi"],
            n_train=d["n_train"], window=d.get("window"),
            meta=d.get("meta", {}),
        )


def fit(x: np.ndarray, rot_hz: np.ndarray, features: list[str],
        rule: str = "vote", z_feat: float = 3.0, vote_min: int = 3,
        max_z_cut: float = 6.0, hard_z: float | None = None,
        window: dict | None = None,
        min_scale_frac: float = 1e-3) -> Baseline:
    """ประมาณเส้นฐานจากข้อมูล**ปกติ**เท่านั้น

    ใช้**ส่วนเบี่ยงเบนมาตรฐาน**ของเศษเหลือเป็นตัววัดการกระจายตัว ไม่ใช่ MAD
    เพราะข้อมูลที่ใช้เทรนเป็นข้อมูลปกติทั้งหมดโดยการออกแบบ จึงไม่มีค่าผิดปกติ
    ให้ต้องทน และหางของการแจกแจงคือข้อมูลที่ต้องใช้ตั้งเกณฑ์ ดูเหตุผลเต็มที่หัวไฟล์

    ``min_scale_frac`` กันกรณีตัวชี้วัดที่แทบไม่แปรผันเลย ซึ่งจะทำให้ ``scale``
    เข้าใกล้ศูนย์แล้ว z ระเบิด
    """
    x = np.asarray(x, dtype=float)
    rot = np.asarray(rot_hz, dtype=float)
    if x.shape[0] != rot.shape[0]:
        raise ValueError("จำนวนแถวของ x กับ rot_hz ไม่เท่ากัน")
    if x.shape[1] != len(features):
        raise ValueError("จำนวนคอลัมน์ของ x ไม่เท่ากับจำนวนชื่อตัวชี้วัด")
    if rule not in ("max_z", "vote"):
        raise ValueError(f"rule ต้องเป็น max_z หรือ vote ไม่ใช่ {rule!r}")

    slope, intercept, scale, use_log = [], [], [], []
    for i, name in enumerate(features):
        col = x[:, i].astype(float)
        lg = _needs_log(name) and np.all(col[np.isfinite(col)] > 0)
        t = np.log(col) if lg else col
        ok = np.isfinite(t)
        if ok.sum() < 3:
            # ตัวชี้วัดที่ใช้ไม่ได้ ตั้งให้ z เป็นศูนย์เสมอโดยให้ scale ใหญ่มาก
            slope.append(0.0)
            intercept.append(float(np.nanmedian(t)) if ok.any() else 0.0)
            scale.append(float("inf"))
            use_log.append(bool(lg))
            continue
        b, a = np.polyfit(rot[ok], t[ok], 1)
        resid = t[ok] - (a + b * rot[ok])
        # ddof=2 เพราะเสียองศาอิสระไปสองตัวกับการประมาณความชันและจุดตัด
        n = int(ok.sum())
        s = float(np.std(resid, ddof=2)) if n > 2 else float(np.std(resid))
        floor = min_scale_frac * float(np.std(t[ok])) if np.std(t[ok]) > 0 else 1e-12
        slope.append(float(b))
        intercept.append(float(a))
        scale.append(max(s, floor, 1e-12))
        use_log.append(bool(lg))

    return Baseline(
        features=list(features), slope=slope, intercept=intercept, scale=scale,
        use_log=use_log, rule=rule, z_feat=z_feat, vote_min=vote_min,
        max_z_cut=max_z_cut, hard_z=hard_z, window=window,
        speed_lo=float(np.min(rot)), speed_hi=float(np.max(rot)),
        n_train=int(x.shape[0]),
        meta={"messages_per_day": MESSAGES_PER_DAY, "scale": "std(resid, ddof=2)"},
    )


class AlarmGate:
    """ด่านยืนยันซ้ำ — เตือนเมื่อ k ใน m ข้อความล่าสุดผิดปกติ

    ## 🚨 ทำไมต้องมีด่านนี้ ไม่ใช่เตือนทันทีที่ข้อความเดียวผิดปกติ

    ที่คาบส่ง 10 วินาที ระบบได้ **8,640 ข้อความต่อวัน** ถ้าต้องการเตือนผิด
    ไม่เกิน 1 ครั้งต่อวัน อัตราการเตือนผิดต่อข้อความต้องไม่เกิน **1.2 x 10⁻⁴**

    **ประมาณค่าระดับนั้นจากไฟล์ปกติ 29 ไฟล์ไม่ได้** เพราะต้องมีตัวอย่าง
    หลักหมื่นขึ้นไปจึงจะเห็นเหตุการณ์ที่เกิด 1 ใน 8,000 ครั้ง
    **นี่เป็นข้อจำกัดของข้อมูล ไม่ใช่ของวิธี** และจะเจอเหมือนกันที่หน้างาน
    ช่วงแรกที่เพิ่งติดตั้งเซ็นเซอร์

    **ทางออกที่วงการ condition monitoring ใช้คือการยืนยันซ้ำตามเวลา**
    อาศัยข้อเท็จจริงทางฟิสิกส์ว่า

    * **ความเสียหายจริงอยู่ต่อเนื่อง** ตลับลูกปืนที่เริ่มแตกไม่หายไปเองในนาทีถัดไป
    * **สัญญาณรบกวนไม่อยู่ต่อเนื่อง** การกระแทกครั้งเดียว ไฟตก หรือคนเดินชน
      กระทบข้อความเดียวแล้วหายไป

    ถ้าอัตราการเตือนผิดต่อข้อความเป็น ``p`` และต้องการ k ใน m ข้อความติดกัน
    โอกาสเตือนผิดลดลงเป็นราว ``C(m,k) x p^k`` ซึ่งลดลงแบบยกกำลัง

        p = 0.05  k=3 m=5  ->  ~1.3 x 10⁻³ ต่อหน้าต่าง  ->  ~11 ครั้งต่อวัน
        p = 0.05  k=4 m=5  ->  ~3.1 x 10⁻⁵ ต่อหน้าต่าง  ->  ~0.3 ครั้งต่อวัน

    **ราคาที่จ่ายคือความหน่วง** ต้องรอ k ข้อความจึงเตือนได้
    ที่คาบ 10 วินาที k=4 คือหน่วง 40 วินาที ซึ่งยอมรับได้สำหรับความเสียหาย
    ที่พัฒนาเป็นวันหรือสัปดาห์ แต่ยอมรับไม่ได้ถ้าต้องจับเหตุการณ์ฉับพลัน
    จึงควรมีช่องทางเตือนทันทีแยกสำหรับค่าที่สูงมากอย่างชัดเจน (``hard_z``)

    ⚠️ **``hard_z`` ต้องตั้งจากการแจกแจงของไฟล์ปกติ ไม่ใช่เดา** ถ้าตั้งต่ำกว่า
    ค่าที่ไฟล์ปกติทำได้ ข้อความปกติจะข้ามด่านนี้ได้ แล้วการรับประกันอัตรา
    การเตือนผิดทั้งหมดเป็นโมฆะ ค่าปริยายจึงเป็น ``None`` คือปิดช่องทางนี้ไว้
    """

    def __init__(self, k: int = 4, m: int = 5, hard_z: float | None = None):
        if not 1 <= k <= m:
            raise ValueError("ต้องมี 1 <= k <= m")
        self.k, self.m, self.hard_z = k, m, hard_z
        self._hist: list[bool] = []

    def update(self, anomaly: bool, max_z: float = 0.0) -> dict:
        """ใส่ผลของข้อความใหม่ คืนสถานะของด่าน"""
        self._hist.append(bool(anomaly))
        if len(self._hist) > self.m:
            self._hist.pop(0)
        votes = sum(self._hist)
        immediate = self.hard_z is not None and max_z > self.hard_z
        return {
            "alarm": bool(votes >= self.k or immediate),
            "immediate": bool(immediate),
            "votes": int(votes),
            "window": len(self._hist),
            "needed": self.k,
        }

    def reset(self) -> None:
        self._hist.clear()


def p_upper_bound(events: int, n: int, conf: float = 0.95) -> float:
    """ขอบบนของความน่าจะเป็น ที่ระดับความเชื่อมั่น ``conf`` (Clopper-Pearson ด้านเดียว)

    ## 🚨 ทำไมต้องใช้ขอบบน ไม่ใช่ค่าที่วัดได้ตรงๆ

    ถ้าทดสอบ 47 ตัวอย่างแล้ว**ไม่พบการเตือนผิดเลย** ค่าที่วัดได้คือ 0
    แต่การสรุปว่า "อัตราการเตือนผิดเป็นศูนย์" **ผิด** เพราะเหตุการณ์ที่เกิด
    1 ใน 100 ครั้ง ก็มีโอกาสสูงที่จะไม่โผล่ในตัวอย่าง 47 ตัว

    สิ่งที่พูดได้อย่างซื่อสัตย์คือ "อัตราการเตือนผิดไม่เกินเท่าไร"
    ซึ่งคือขอบบนนี้ สำหรับกรณีไม่พบเหตุการณ์เลย ค่าประมาณคือ ``3/n``
    (กฎสามส่วน) เช่น n = 47 ได้ขอบบนราว 6%

    **การรายงาน "เตือนผิด 0 ครั้งต่อวัน" จากการเห็นศูนย์เหตุการณ์
    เป็นการเคลมเกินข้อมูล** และเป็นกับดักตระกูลเดียวกับการรายงาน
    accuracy 99% จากการแบ่งข้อมูลที่รั่ว
    """
    if not 0 <= events <= n:
        raise ValueError("ต้องมี 0 <= events <= n")
    if n == 0:
        return 1.0
    if events == n:
        return 1.0
    alpha = 1.0 - conf
    # หา p ที่ทำให้ P(X <= events | n, p) = alpha ด้วยการแบ่งครึ่ง
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        cdf = sum(math.comb(n, j) * mid ** j * (1 - mid) ** (n - j)
                  for j in range(events + 1))
        if cdf > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def alarms_per_day(p: float, k: int, m: int,
                   messages_per_day: int = MESSAGES_PER_DAY) -> float:
    """ประมาณจำนวนการเตือนผิดต่อวันหลังผ่านด่านยืนยันซ้ำ k ใน m

    สมมติว่าข้อความแต่ละข้อความเป็นอิสระต่อกัน ซึ่ง**ไม่จริงเสียทีเดียว**
    เพราะสัญญาณรบกวนที่กินเวลานานกว่าคาบส่งจะทำให้ข้อความติดกันสัมพันธ์กัน
    ตัวเลขที่ได้จึงเป็นขอบล่างที่ดีเกินจริง ใช้เทียบทางเลือกได้ แต่ห้ามใช้เป็น
    คำมั่นกับผู้ใช้
    """
    if not 0.0 <= p <= 1.0:
        raise ValueError("p ต้องอยู่ระหว่าง 0 ถึง 1")
    prob = sum(math.comb(m, j) * p ** j * (1 - p) ** (m - j)
               for j in range(k, m + 1))
    return prob * messages_per_day


def loo_scores(x: np.ndarray, rot_hz: np.ndarray, features: list[str],
               z_feat: float = 3.0,
               groups: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """คะแนนของตัวอย่างปกติแต่ละตัว โดยโมเดลที่**ไม่เคยเห็นตัวอย่างนั้น**

    ตัดออกหนึ่งกลุ่ม ประมาณเส้นฐานใหม่จากที่เหลือ แล้วให้คะแนนกลุ่มที่ตัดออก
    ทำซ้ำทุกกลุ่ม (leave-one-group-out)

    **นี่คือวิธีเดียวที่ตั้งเกณฑ์ได้อย่างซื่อสัตย์จากไฟล์ปกติจำนวนน้อย**
    ถ้าตั้งเกณฑ์จากคะแนนของไฟล์ที่โมเดลเห็นแล้ว เกณฑ์จะต่ำเกินจริง
    เพราะโมเดลถูกปรับให้เข้ากับไฟล์เหล่านั้นอยู่แล้ว

    ``groups`` คือสิ่งที่ต้องตัดออกพร้อมกันทั้งก้อน **ค่าเริ่มต้น ``None``
    = หนึ่งแถวหนึ่งกลุ่ม** ซึ่งเป็นพฤติกรรมเดิมสำหรับตารางที่หนึ่งแถว = หนึ่งไฟล์

    🚨 **ถ้าตารางเป็นหนึ่งแถวต่อหน้าต่าง ต้องส่ง ``groups`` เป็นชื่อไฟล์**
    ไม่งั้นโมเดลจะเห็นหน้าต่างพี่น้องของตัวที่ตัดออกอยู่ในชุดเทรน ซึ่งคือ
    leakage ตัวเดียวกับที่วัดไว้ว่ากินไป 27 จุด accuracy แล้วเกณฑ์จะต่ำเกินจริง

    คืน ``(max_z, n_exceed)`` **ต่อแถว** เรียงตามลำดับเดิม
    """
    x = np.asarray(x, dtype=float)
    rot = np.asarray(rot_hz, dtype=float)
    n = x.shape[0]
    g = np.arange(n) if groups is None else np.asarray(groups)
    if g.shape[0] != n:
        raise ValueError("จำนวนแถวของ groups ไม่เท่ากับ x")
    max_z = np.zeros(n)
    n_exceed = np.zeros(n, dtype=int)
    # np.unique ไม่ใช่ pd.unique เพื่อไม่ให้ไฟล์นี้ต้องพึ่ง pandas
    for key in np.unique(g):
        held = g == key
        m = fit(x[~held], rot[~held], features, z_feat=z_feat)
        z = np.abs(m.score_array(x[held], rot[held]))
        max_z[held] = np.nanmax(z, axis=1)
        n_exceed[held] = np.nansum(z > z_feat, axis=1)
    return max_z, n_exceed

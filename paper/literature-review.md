# ทบทวนวรรณกรรม — สรุปงานวิจัย 11 ฉบับ

อ่านเมื่อ 2026-10-02 · **ทุกฉบับใช้ MAFAULDA ชุดเดียวกับเรา**

เอกสารนี้สรุปว่าแต่ละฉบับ **ทำอะไร ทำอย่างไร และได้อะไรออกมา** พร้อมบอกว่า
กระทบงานของเราตรงไหน

---

## 📖 วิธีอ่านการอ้างอิงในเอกสารนี้

ทุกข้ออ้างมีที่มากำกับในรูปแบบ **〔หน้า N · ตำแหน่ง〕** เช่น

> 〔หน้า 3 · Table II〕 — อยู่ในหน้าที่ 3 ของไฟล์ PDF ตาราง Table II
> 〔หน้า 7 · บรรทัด ~29〕 — อยู่ในหน้าที่ 7 ประมาณบรรทัดที่ 29 ของหน้านั้น

**หมายเหตุสำคัญเรื่องเลขบรรทัด** ไฟล์ PDF ของงานวิจัยไม่มีเลขบรรทัดกำกับมาจริง
และเกือบทุกฉบับเป็น **สองคอลัมน์** ซึ่งทำให้ลำดับบรรทัดที่สกัดข้อความออกมาได้
**ไม่ตรงกับลำดับที่ตาเห็น** เลขบรรทัดที่ให้ไว้จึงเป็นค่าประมาณจากการสกัดข้อความ
ใช้เป็นตัวช่วยคร่าวๆ เท่านั้น

**วิธีที่เชื่อถือได้ที่สุดคือค้นข้อความต้นฉบับ** ทุกข้ออ้างที่สำคัญจึงมี
**ข้อความภาษาอังกฤษต้นฉบับยกมาตรงๆ** ให้ `Ctrl+F` ในไฟล์ PDF ได้ทันที
ส่วนตัวเลขทั้งหมดบอกชื่อตารางไว้ ซึ่งหาได้แม่นกว่าเลขบรรทัด

**เลขหน้า** นับจากหน้าแรกของไฟล์ PDF (= 1) ไม่ใช่เลขหน้าที่พิมพ์ในวารสาร
สำหรับฉบับ 02 (IEEE Access) ซึ่งพิมพ์เลขหน้าวารสารไว้ด้วย
เลขวารสาร = 120761 + เลขหน้า PDF

### 🔘 ปุ่มเปิดเอกสาร

ทุกหัวข้อของแต่ละฉบับมี**แถบปุ่ม**อยู่ใต้ชื่อเรื่อง กดแล้วเปิดไฟล์ PDF ได้เลย

| ปุ่ม | ทำอะไร |
|---|---|
| **📄 เปิดเอกสาร** | เปิดไฟล์ PDF ฉบับนั้นจากหน้าแรก |
| **หน้า 3** | เปิดไฟล์ PDF **แล้วกระโดดไปหน้า 3** ทันที |
| **⬆ ดัชนี** | กลับขึ้นไปตารางดัชนีด้านบน |

**ต้องกดจากโหมด Preview** ใน VS Code กด `Ctrl+Shift+V` เพื่อเปิด Markdown Preview
ก่อน แล้วปุ่มจะกดได้ (ถ้าดูจากโหมดแก้ไขธรรมดาจะเห็นเป็นข้อความเฉยๆ)

⚠️ **ปุ่มกระโดดหน้าใช้ได้กับโปรแกรมอ่าน PDF บางตัวเท่านั้น** `#page=N` ทำงานใน
Chrome, Edge, Adobe Acrobat และส่วนขยาย vscode-pdf ถ้าเครื่องเปิด PDF ด้วย
โปรแกรมที่ไม่รองรับ มันจะเปิดไฟล์ให้แต่ไปที่หน้าแรก **แล้วค่อยพิมพ์เลขหน้าเอง
หรือใช้ `Ctrl+F` ค้นข้อความต้นฉบับที่ยกมาให้**

📌 **ลิงก์ทั้งหมดผูกกับชื่อไฟล์ PDF ปัจจุบัน** ถ้าเปลี่ยนชื่อไฟล์หรือย้ายที่
ปุ่มจะเสีย (ไฟล์ PDF ไม่ขึ้น git เพราะติดลิขสิทธิ์ จึงมีอยู่แต่บนเครื่องเรา)
รายการลิงก์อยู่ท้ายไฟล์นี้ในหัวข้อ **ที่อยู่ของไฟล์เอกสาร**

---

## สรุปสั้นที่สุด — 6 เรื่องที่เปลี่ยนไปหลังอ่าน

| | เรื่อง | ผล |
|---|---|---|
| 1 | **ตัวเลข 96–99% ที่เห็นในทุกฉบับ มาจากการแบ่งข้อมูลที่รั่ว** | การทดลอง leakage ของเรา**ทำนายตัวเลขเหล่านั้นได้** ✅ |
| 2 | **แกน tangential ดีที่สุด radial แย่ที่สุด** | มีงานทดลอง 120 รอบยืนยันที่เราวัดเอง ✅ |
| 3 | **ลายเซ็นข้ามฝั่งมีจริง** | มีงานอื่นเจอแบบเดียวกัน ไม่ใช่ร่องรอยของรอบบันทึก ✅ |
| 4 | **order tracking มีจริงและเขาใช้ tachometer เหมือนเรา** | ปิดคำถามข้อ 1 ที่ค้างมานาน ✅ |
| 5 | **Random Forest คือมาตรฐานจริง** | 5 ฉบับเลือกด้วยเหตุผลเดียวกับเรา ✅ |
| 6 | 🔄 **การตัดช่อง `mic` ออกของเราอาจผิด** | 2 ฉบับบอกว่า mic เป็นช่องที่ดีที่สุด ❗ |

---

<a id="index"></a>

## 🔘 ตารางดัชนี — กดเปิดเอกสารได้เลย

เรียงตามความสำคัญกับงานของเรา **กดคอลัมน์ 📄 เพื่อเปิด PDF · กดคอลัมน์ 📖 เพื่อไปอ่านสรุป**

| # | ชื่อย่อ | ปี · งานประชุม/วารสาร | น. | ⭐ | 📄 เปิด PDF | 📖 สรุป | เหตุผลที่สำคัญ |
|---|---|---|---:|---|---|---|---|
| **08** | **Inverse PINN** (Sanami) | 2026 ACC | 1 | 🔥🔥🔥 | [📄 เปิด][pdf08] | [📖 อ่าน](#paper08) | **order tracking จริง** ตอบคำถามข้อ 1 |
| **10** | **Factor Effects / Signal-to-Image** (Kim) | 2025 ISPA | 4 | 🔥🔥🔥 | [📄 เปิด][pdf10] | [📖 อ่าน](#paper10) | **ทดลอง 120 รอบว่าแกนไหนดี** ยืนยันของเรา |
| **05** | **Comparison of ML Models** (Carvalho) | 2025 LCIoT | 4 | 🔥🔥🔥 | [📄 เปิด][pdf05] | [📖 อ่าน](#paper05) | **หลักฐาน leakage ที่ชัดที่สุด** 99.11% |
| **02** | **Two-Stage Hybrid** (Costa) | 2026 IEEE Access | 16 | 🔥🔥 | [📄 เปิด][pdf02] | [📖 อ่าน](#paper02) | ยืนยัน RF + Isolation Forest + ชี้ช่องว่างในออกแบบเรา |
| **01** | **Lightweight Edge Fusion** (Jiang) | 2026 ICETCI | 6 | 🔥🔥 | [📄 เปิด][pdf01] | [📖 อ่าน](#paper01) | **สถาปัตยกรรมเดียวกับเรา** + RF |
| **06** | **Cutting-Edge Anomaly Detection** (Ūselis) | 2024 AIEEE | 4 | 🔥🔥 | [📄 เปิด][pdf06] | [📖 อ่าน](#paper06) | ลายเซ็นข้ามฝั่ง + mic ชนะทุกช่อง |
| **11** | **Handling Imbalance Classes** (Ali) | 2019 ICMSAO | 5 | 🔥 | [📄 เปิด][pdf11] | [📖 อ่าน](#paper11) | **ใช้ความเร็วรอบเป็น feature** |
| **04** | **SMOTE + DNN** (Bingamil) | 2022 IECON | 6 | 🔥 | [📄 เปิด][pdf04] | [📖 อ่าน](#paper04) | ตัวอย่าง SMOTE รั่ว |
| **09** | **Hybrid Models** (Al Maruf) | 2025 COMPAS | 6 | 🟡 | [📄 เปิด][pdf09] | [📖 อ่าน](#paper09) | เทียบ 6 โมเดลพื้นฐาน |
| **07** | **Denoising Autoencoder** (Tran) | 2023 SAS | 6 | 🟡 | [📄 เปิด][pdf07] | [📖 อ่าน](#paper07) | **ฉบับเดียวที่เอ่ยถึง 51,200 Hz** |
| **03** | **Almost-periods** (Avkhimenko) | 2023 MLSD | 5 | ⬜ | [📄 เปิด][pdf03] | [📖 อ่าน](#paper03) | คณิตศาสตร์ล้วน ใช้แค่ 3 สัญญาณ |

**ถ้ามีเวลาอ่านแค่ฉบับเดียว** → [**08 Inverse PINN**][pdf08] แค่หน้าเดียว
และเป็นคำตอบของปัญหาที่ใหญ่ที่สุดที่เราค้างอยู่

**ถ้าจะเอาไปตอบอาจารย์** → [**10 Factor Effects**][pdf10] หน้า 3 ตาราง Table II
เพราะเป็นตารางเดียวที่ยืนยันการเลือกช่องเซ็นเซอร์ของเราด้วยการทดลอง 120 รอบ

---

# ส่วนที่ 1 — ฉบับที่สำคัญที่สุด

<a id="paper08"></a>

## 08 · Inverse Physics-Informed Neural Networks

**Sanami, S. & Aghdam, A. G.** — Concordia University, Montreal
*American Control Conference (ACC) 2026*, New Orleans, 27–29 พ.ค. 2026, หน้า 2362

> 🔘 [**📄 เปิดเอกสาร**][pdf08] · ทั้งฉบับมี [หน้า 1][pdf08p1] หน้าเดียว · [⬆ ดัชนี](#index)

### เขาทำอะไร
แก้ปัญหาที่เขาระบุไว้ตรงๆ ในบทนำว่า 〔หน้า 1 · บรรทัด ~25〕

> *"Fault classification in rotating machinery is challenging because vibration
> signals are periodic, noisy, and **strongly affected by operating speed**.
> Traditional time-, frequency-, and time-frequency-domain methods can be
> effective, but their performance often degrades under variable rotational
> conditions."*

**นี่คือปัญหาเดียวกับที่เราวัดได้ว่า `o_axial` กระโดด 4 เท่าเมื่อความเร็วข้าม 50 Hz**

### ทำอย่างไร — ส่วนที่มีค่าที่สุด

ขั้นแรกคือ **revolution-synchronous preprocessing** 〔หน้า 1 · หัวข้อ II Methodology
บรรทัด ~40〕

> *"The continuous vibration signal is **segmented revolution-by-revolution using
> the tachometer signal**. Each revolution is **normalized to a phase variable
> ϕ ∈ [0, 2π]**, enabling a cycle-consistent representation even when the speed
> varies."*

**นี่คือ angular resampling / order tracking ที่เราค้นหาอยู่** และทำจาก
**สัญญาณ tachometer** ซึ่งเราถอดรหัสไว้แล้ว

ขั้นต่อมาฝังแบบจำลองโรเตอร์ 2 องศาอิสระเข้าไปใน loss ของ neural network
〔หน้า 1 · สมการ (1) บรรทัด ~45〕

```
mᵢ ẍᵢ + cᵢ(ω) ẋᵢ + kᵢ(ω) xᵢ = Fᵢ(φ)        i = 1, 2
```

โดย *"cᵢ(ω) and kᵢ(ω) denote **speed-dependent damping and stiffness**"*
〔หน้า 1 · บรรทัด ~47〕 แล้วเอาค่าที่ประมาณได้ (c₁, c₂, k₁, k₂) ไปเป็น feature

> *"The resulting estimated parameters (c1,c2,k1,k2) are then aggregated and used
> as input features to a **random forest classifier** for fault identification."*
> 〔หน้า 1 · บรรทัด ~55〕

### ได้อะไรออกมา
- ทดลองบน MAFAULDA 3 คลาส คือ normal, vertical misalignment, horizontal misalignment
- ค่า damping และ stiffness ที่ประมาณได้แปรตามความเร็วและชนิดความเสียหายอย่างมีแบบแผน
- **จำแนกได้ดีแม้เจอระดับความรุนแรงที่ไม่เคยเห็นตอนเทรน** 〔หน้า 1 · บรรทัด ~21 และ ~68〕
  > *"including **generalization to unseen variations in misalignment severity**"*
- ชนะ baseline 〔หน้า 1 · บรรทัด ~69〕
  > *"baseline methods such as **KNN and shapelet-based learning** show
  > substantially lower macro-average performance"*

### 🚩 กระทบเราอย่างไร

**✅ ปิดคำถามข้อ 1 ได้** order tracking เป็นเทคนิคที่มีจริงในงานตีพิมพ์ ใช้บน
MAFAULDA ได้ และ**ใช้ tachometer ที่เราถอดรหัสไว้แล้วเป็นวัตถุดิบ**
→ งานใน `src/data/tachometer.py` (แก้กับดักพัลส์กว้าง พัลส์หยัก และวิธีนับปลายถึงปลาย)
**ไม่ได้เสียเปล่า มันคือขั้นแรกของเทคนิคนี้พอดี**

**✅ ยืนยันว่าการทดสอบข้ามระดับความรุนแรงเป็นเกณฑ์ที่ถูก** เราคิดเกณฑ์นี้ขึ้นเอง
ตอนทำ `src/features/check_signature_persistence.py` เขาใช้เกณฑ์เดียวกัน

**✅ Random Forest อีกฉบับ**

### ⚠️ จุดอ่อน
**เป็นบทคัดย่อขยาย 1 หน้า ไม่มีตัวเลขเลยแม้แต่ตัวเดียว** ไม่มีตาราง ไม่มี accuracy
ตรวจสอบไม่ได้ และ PINN หนักเกินจะรันบน ESP32

**แต่ส่วนที่เราเอามาใช้คือ preprocessing ไม่ใช่ PINN** — การแปลงจาก "ต่อเวลา"
เป็น "ต่อมุมเพลา" คำนวณเบามาก (แค่ interpolate) และทำบน Pi ได้สบาย

---

<a id="paper10"></a>

## 10 · Quantifying Factor Effects in Signal-to-Image

**Kim, J. W. & Bae, Y. S.** — Tech University of Korea
*14th International Symposium on Image and Signal Processing and Analysis (ISPA) 2025*,
Coimbra, Portugal · DOI 10.1109/ISPA66905.2025.11259102 · หน้าวารสาร 204–207

> 🔘 [**📄 เปิดเอกสาร**][pdf10] · ไปหน้า [2 (วิธีการ + การแบ่งข้อมูล)][pdf10p2]
> · [**3 (ตารางผลทั้งหมด)**][pdf10p3] · [⬆ ดัชนี](#index)

### เขาทำอะไร
สังเกตว่างานก่อนหน้า **ตั้งค่าตัวแปรสำคัญไว้ตายตัวแล้วไม่เคยวัดว่ามันสำคัญแค่ไหน**
จึงทำการทดลองแบบ **full-factorial 2 × 4 × 3 × 5 = 120 รอบ** โดยตรึงตัวจำแนก
(ResNet-50) ไว้ แล้วไล่เปลี่ยนตัวแปร 4 ตัว

### ทำอย่างไร

| ตัวแปร | ค่าที่ลอง |
|---|---|
| ตำแหน่งตลับลูกปืน | inner (underhang) / outer (overhang) |
| **แกนเซ็นเซอร์** | axial / radial / tangential / tri-axial |
| **ความยาวหน้าต่าง** | 256 / 1,024 / 4,096 แถว |
| วิธีแปลงสัญญาณเป็นภาพ | STIM / GADF / MTF / SDP / RP |

**เกณฑ์การเลือกความยาวหน้าต่าง** 〔หน้า 2 · หัวข้อ IV-B บรรทัด ~61〕

> *"Zhong showed that diagnostic accuracy improves when the input window spans
> **at least one full mechanical revolution** [17]. Let fs be the sampling rate;
> the samples per revolution are **Nrev(r) = 60 fs / RPM(r)**."*

**การแบ่งข้อมูล** 〔หน้า 2 · หัวข้อ IV-B บรรทัด ~70〕

> *"We then perform an 80/20 train/test split at the window level, **keeping all
> ten windows from a given record in the same split to avoid leakage**."*

**ข้อมูลที่ใช้** 〔หน้า 2 · หัวข้อ IV-A บรรทัด ~47〕

> *"MAFAULDA dataset [3] contains **1,951 five-second records sampled at 50 kHz**
> on a rotating-machinery rig operating from **720–3,600 RPM**."*

(จำนวน 1,951 ไฟล์ตรงกับที่เรานับได้ ✅ ส่วน 50 kHz ผิด 🚩)

### ได้อะไรออกมา — 🔥 ตารางที่สำคัญที่สุดสำหรับเรา

**แกนเซ็นเซอร์** 〔หน้า 3 · **Table II** บรรทัด ~19〕

| แกน | accuracy เฉลี่ย | SD | |
|---|---:|---:|---|
| **radial** | **58.36%** | 16.61 | ← **แย่ที่สุด** |
| axial | 64.17% | 19.60 | |
| **tangential** | **72.19%** | 18.68 | ← **ดีที่สุดในบรรดาแกนเดี่ยว** |
| tri-axial (รวม 3 แกน) | 78.73% | 17.62 | |

คำอธิบายของเขา 〔หน้า 3 · บรรทัด ~1〕
> *"among single axes, **tangential leads while radial lags**, reflecting
> axis-dependent sensitivity to fault-induced vibrational modes."*

**ความยาวหน้าต่าง** 〔หน้า 3 · **Table III** บรรทัด ~25〕

| แถว | accuracy | SD |
|---|---:|---:|
| 256 | 55.76% | 17.26 |
| 1,024 | 70.73% | 18.72 |
| 4,096 | **77.84%** | 16.24 |

**ตำแหน่งตลับลูกปืน** 〔หน้า 3 · **Table I** บรรทัด ~15〕
inner 67.46% · outer 68.77% → ต่างกันน้อย เป็นตัวแปรรอง

**วิธีแปลงเป็นภาพ** 〔หน้า 3 · **Table IV**〕
STIM 80.38% · GADF 78.0% · RP 69.41% · MTF 68.09% · SDP 44.67%

**สามอันดับแรกจาก 120 รอบ** 〔หน้า 3 · **Table VI** บรรทัด ~80〕

| วิธีแปลง | แกน | ตำแหน่ง | หน้าต่าง | accuracy |
|---|---|---|---:|---:|
| STIM | tri-axial | inner | 4,096 | **98.51%** |
| STIM | tri-axial | outer | 4,096 | 98.36% |
| STIM | **tangential** | outer | 4,096 | 97.77% |

**ตารางเทียบกับงาน MAFAULDA ก่อนหน้า** 〔หน้า 3 · **Table VII** บรรทัด ~85〕

| ผู้แต่ง | วิธี | accuracy |
|---|---|---:|
| Ūselis (= ฉบับ 06 ของเรา) | feature extraction + XGBoost | 96.02% |
| Ali (= ฉบับ 11 ของเรา) | feature extraction + MLP | 96.2% |
| Khan | CWT scalogram + ResNet-18 | 96.36% |
| Wang | GAF + WPorNet | 96.45% |
| **ของเขา** | STIM + ResNet-50 | **98.51%** |

### 🚩 กระทบเราอย่างไร — ยืนยันงานของเราสองเรื่องใหญ่

**✅ ยืนยันว่า `radial` เป็นช่องที่แย่ และ tangential เป็นช่องที่ดี**

เราค้นพบเรื่องนี้เองและเขียนไว้ใน `CLAUDE.md` หัวข้อ 5 ว่า

> **`u_radial` มองไม่เห็น misalignment เลย** ทุกตัวเลขอยู่ที่ 0.8–1.0
> กราฟ EDA รูป 01–05 ใช้ช่องนี้ทั้งหมด จึงสรุปเรื่อง misalignment จากรูปพวกนั้นไม่ได้
>
> **`o_tang` คือช่องที่ต้องใช้กับ misalignment** · **`u_tang` คือช่องที่ดีที่สุดสำหรับ imbalance**

**งานนี้ทำการทดลอง 120 รอบแล้วได้ลำดับเดียวกันเป๊ะ — radial แย่สุด tangential ดีสุด
ห่างกัน 14 จุด** → นี่คือ**ขาที่สองของหลักฐาน**ที่อาจารย์ต้องการ

**✅ ยืนยันว่าหน้าต่าง 32,768 แถวของเรามีเหตุผลรองรับ**

ใช้เกณฑ์ `Nrev = fs / rot_hz` ของเขา แต่แทนด้วย fs ที่ถูกคือ 51,200 Hz

| | ที่ 12.3 Hz (ช้าสุด) | ที่ 60 Hz (เร็วสุด) |
|---|---:|---:|
| 1 รอบ กินกี่แถว | 4,163 | 853 |
| **หน้าต่างของเขา 4,096 แถว** | **0.98 รอบ** ⚠️ | 4.8 รอบ |
| **หน้าต่างของเรา 32,768 แถว** | **7.9 รอบ** ✅ | 38 รอบ |

**หน้าต่างที่ยาวที่สุดของเขายังไม่ครบหนึ่งรอบที่ความเร็วต่ำสุด** ขณะที่ของเราครบ 7.9 รอบ
และ accuracy ของเขาเพิ่มขึ้นเรื่อยๆ ตามความยาวโดยยังไม่อิ่มตัว
→ **การเลือกหน้าต่างใหญ่ของเราถูกทาง**

### ⚠️ จุดอ่อน
- **ระบุ fs = 50 kHz** 🚩 〔หน้า 2 · บรรทัด ~48〕 และใช้ค่านี้คำนวณแถวต่อรอบด้วย
  → ตัวเลข 806–4,166 แถวต่อรอบของเขาคลาด 2.4%
- **ไม่คุมมวลถ่วง** ใช้ไฟล์ทุกมวล → คลาส bearing มี imbalance ปนอยู่
- **ไม่คุมความเร็วรอบ** → leakage ช่องทางที่เราวัดได้ยังเปิดอยู่
- signal-to-image + ResNet-50 **รันบน edge ไม่ได้** (เขาใช้ RTX 3090 เทรน
  และวัดเวลาแปลงภาพบน AMD Ryzen 5 9600X 〔หน้า 2 · หัวข้อ V-A〕)

---

<a id="paper05"></a>

## 05 · Comparison of Machine Learning Models

**Carvalho, L. S., Braga, G., Kastensmidt, F., Beck, A. C. S. & Azambuja, J. R. F.**
Federal University of Rio Grande do Sul (UFRGS), Porto Alegre, Brazil
*IEEE Latin Conference on IoT (LCIoT) 2025* · DOI 10.1109/LCIoT64881.2025.11118566

> 🔘 [**📄 เปิดเอกสาร**][pdf05] · ไปหน้า [**3 (วิธีการ + ประโยคเรื่องการแบ่ง 70/30)**][pdf05p3]
> · [4 (ตารางผลและตารางเวลา)][pdf05p4] · [⬆ ดัชนี](#index)

### เขาทำอะไร
เทียบ MLP / CNN / GRU / LSTM บน MAFAULDA โดยวัดทั้ง accuracy และเวลาที่ใช้

### ทำอย่างไร
〔หน้า 3 · หัวข้อ IV บรรทัด ~45–55〕

> *"Preprocessing involved applying the Fast Fourier Transform (FFT) to convert
> time-domain signals into the frequency domain. From the resulting spectrum,
> **four statistical features** were extracted: the mean amplitude, standard
> deviation of amplitudes, and the minimum and maximum values... The analysis was
> conducted using two windowing strategies: **fixed windows of 1000 samples and
> overlapping windows with a 50% overlap**... **The dataset was then split into
> 70% for training and 30% for inference** to ensure robust model evaluation."*

🚩 **ไม่มีคำใดเลยเรื่องการจัดกลุ่มตามไฟล์** — ประโยคเรื่องการแบ่งจบลงตรงนั้น

ข้อมูล 〔หน้า 3 · บรรทัด ~35〕 *"a sampling rate of **50 kHz** for 5 seconds,
totaling 250,000 points per sample... **1,951 scenarios**... **49 scenarios**
correspond to normal operation, and **197 scenarios** to parallel misalignment"*
(จำนวนไฟล์ตรงกับเรา ✅)

### ได้อะไรออกมา

**accuracy** 〔หน้า 4 · **Table II** (ซ้อน 50%) และ **Table III** (หน้าต่างชิดกัน)〕

| โมเดล | หน้าต่างชิดกัน | ซ้อนทับ 50% |
|---|---:|---:|
| **MLP** | **99.11%** | 97.57% |
| LSTM | 94.70% | **98.70%** |
| GRU | 96.52% | 97.66% |
| CNN | 94.38% | 92.98% |

**เวลา (ไมโครวินาทีต่อหน้าต่าง)** 〔หน้า 4 · **Table IV** บรรทัด ~56〕

| | MLP | CNN | GRU | LSTM |
|---|---:|---:|---:|---:|
| Training (ชิดกัน) | **762** | 50,317 | 93,158 | 82,049 |
| **Inference (ชิดกัน)** | **56** | 358 | 2,885 | 733 |

### 🚩🚩🚩 กระทบเราอย่างไร — นี่คือหลักฐานที่เราต้องการที่สุด

**การตั้งค่าของเขาคือเงื่อนไข `random-window` ในการทดลอง leakage ของเราเป๊ะทุกข้อ**

| | การทดลองของเรา | งานของเขา |
|---|---|---|
| ตัดไฟล์เป็นหน้าต่าง | ✅ | ✅ 250 หน้าต่างต่อไฟล์ |
| สุ่มแบ่งระดับหน้าต่าง | ✅ | ✅ 70/30 ไม่จัดกลุ่ม |
| **accuracy ที่ได้** | **0.996** | **0.9911** |

**เราวัดไว้ล่วงหน้าแล้วว่าการแบ่งแบบนี้ให้ 0.996 เขาได้ 0.9911**
(ดู `experiments/2026-09-25-split-leakage.md`)

และมีสองอย่างที่ทำให้แน่ใจขึ้นอีก

1. **หน้าต่าง 1,000 แถว = 20 ms ไม่ครบหนึ่งรอบการหมุนที่ความเร็วใดเลย**
   (ที่ 30 Hz ต้องใช้ 1,707 แถว) โมเดลจึง**มองไม่เห็นการหมุนครบรอบแม้แต่รอบเดียว**
   — ซึ่งขัดกับเกณฑ์ที่ฉบับ 10 อ้างไว้ 〔ฉบับ 10 หน้า 2 บรรทัด ~61〕
2. **ใช้แค่ 4 feature** แยก 6 คลาสได้ 99.11% — ด้วย 4 ตัวเลขจากสเปกตรัม
   เป็นไปไม่ได้ทางฟิสิกส์ที่จะแยกความเสียหาย 6 ชนิดได้ขนาดนั้น

> **ข้อสรุป** ผลของเขาเกือบทั้งหมดคือโมเดล**จำไฟล์ได้** ไม่ใช่จำความเสียหายได้
> และ `src/models/leakage_demo.py` ของเรา**ทำนายตัวเลขนี้ไว้ก่อนที่เราจะอ่านงานนี้**

**นี่คือคำตอบตรงๆ ของคำถามข้อ 2 ใน `paper/README.md`** ที่เราเขียนไว้ว่า
*"ถ้าเจองานที่รายงาน 99% ด้วยการสุ่มหน้าต่าง → ยืนยันว่าข้อสังเกตของเราถูก
และกลายเป็นจุดแข็งของรายงานเรา"* — **เจอแล้ว**

### ✅ ของที่ใช้ได้
**ตารางเวลา inference** ซึ่งหายากในวรรณกรรม **MLP inference 56 µs เบากว่า
GRU 51 เท่า** → สนับสนุนการเลือกโมเดลเบาสำหรับ edge
(แต่ไม่ระบุว่าวัดบนฮาร์ดแวร์อะไร จึงใช้เทียบอัตราส่วนได้ แต่ใช้เป็นค่าสัมบูรณ์ไม่ได้)

---

<a id="paper02"></a>

## 02 · A Two-Stage Hybrid Architecture for Unknown Anomaly Detection

**Costa, A. C. M., de Melo, P. H. A. D., da Silveira, A. W. F. V., dos Santos, M. B.
& Gomes, L. C.** — Federal University of Uberlândia (UFU) และ
Federal University of Viçosa (UFV), **บราซิล** (ประเทศเดียวกับที่ทำ MAFAULDA ซึ่งมาจาก UFRJ)
*IEEE Access*, vol. 14, 2026 · DOI [10.1109/ACCESS.2026.3719574](https://doi.org/10.1109/ACCESS.2026.3719574)
**Open Access (CC-BY)** 16 หน้า · รับ 15 ก.ค. 2026 ตีพิมพ์ 3 ส.ค. 2026

> 🔘 [**📄 เปิดเอกสาร**][pdf02] · ไปหน้า [1][pdf02p1] [3][pdf02p3] [4][pdf02p4]
> [5][pdf02p5] [**6–7 (ข้อมูล + feature)**][pdf02p6] [7][pdf02p7]
> [**10 (ตาราง ML vs DL)**][pdf02p10] [11][pdf02p11] [12][pdf02p12]
> [**13 (ผลรวม + ข้อจำกัด)**][pdf02p13] [14][pdf02p14] · [⬆ ดัชนี](#index)

> เลขหน้าวารสาร = 120761 + เลขหน้า PDF (เช่น หน้า PDF 7 = หน้าวารสาร 120768)

### เขาทำอะไร
แก้ปัญหาที่ว่า **classifier แบบ supervised เมื่อเจอความเสียหายชนิดที่ไม่เคยเห็น
ตอนเทรน มันจะตอบผิดอย่างมั่นใจ** ซึ่งเป็นสถานการณ์จริงในโรงงาน เพราะไม่มีทาง
เก็บตัวอย่างความเสียหายได้ครบทุกชนิดก่อนติดตั้ง 〔หน้า 1 · Abstract〕

```
สัญญาณ → ชั้น 1: supervised classifier → คืน posterior probability
       → ถ้ามั่นใจ ≥ τ  → ตอบ Known Fault คลาสนั้นเลย
       → ถ้ามั่นใจ < τ  → ส่งต่อชั้น 2: one-class detector (เทรนจาก Normal เท่านั้น)
                        → ตอบ Normal Operation หรือ Unknown Anomaly
```

ผลลัพธ์มี **3 ทาง** คือ `Normal Operation` / `Known Fault` / **`Unknown Anomaly`**
จุดขายคือ **เมื่อมีความเสียหายชนิดใหม่เกิดขึ้น ไม่ต้องเทรนชั้นที่ 2 ใหม่**

### ทำอย่างไร

**ข้อมูล** 〔หน้า 6 · หัวข้อ IV-A บรรทัด ~69〕
> *"The signals were **acquired at a sampling rate of 50 kHz** under controlled
> laboratory conditions."* 🚩

6 คลาสเดียวกับเรา (normal, `mh`, `mv`, `ho`, `hu`, `im`)

**feature — 286 มิติ** 〔หน้า 6–7 · หัวข้อ IV-B〕

> *"**For each signal window**, 286 statistical features were extracted from the
> time and frequency domains, encompassing all the sensor channels."*
> 〔หน้า 6 · บรรทัด ~84〕 🚩 **ไม่ระบุขนาดหน้าต่างเลยทั้งฉบับ**

- **โดเมนเวลา** variance, standard deviation, RMS, peak-to-peak, **kurtosis**,
  **skewness**, **crest factor**
- **โดเมนความถี่** 〔หน้า 7 · บรรทัด ~17〕 *"spectral variance, dominant frequency,
  **spectral entropy**, and band-power ratios"* และอธิบายว่า
  〔หน้า 7 · บรรทัด ~22〕 *"spectral entropy offers a compact measure of spectral
  complexity and non-stationarity"*

**กัน leakage** 〔หน้า 7 · บรรทัด ~29–33〕
> *"The features extracted from the eight acquisition channels were combined into a
> single **286-dimensional feature vector**... all features were standardized to
> zero mean and unit variance using **statistics computed exclusively from the
> training partitions, thereby preventing information leakage** during model
> evaluation."* ✅

**การแบ่ง train/test** 〔หน้า 7 · หัวข้อ IV-C บรรทัด ~45〕 ออกแบบ
**41 experimental blocks** ขึ้นเอง (บอกว่าเป็น contribution ของงานนี้
*"not adapted from prior MAFAULDA-based studies"*) แบ่งสามฉากทัศน์

| ฉากทัศน์ | คลาสตอนทดสอบ | ตัวอย่าง block |
|---|---|---|
| **closed-set** | เหมือนตอนเทรนทุกคลาส | 1, 9, 13 |
| **partial open-set** | เป็น subset ของตอนเทรน | 2–7 |
| **fully open-set** | **ไม่มีอยู่ตอนเทรนเลย** | 3, 31, 35 |

และแยก calibration ออกจาก evaluation 〔หน้า 5 · บรรทัด ~51〕
> *"the 41 experimental blocks were split once, with a fixed random seed, into a
> calibration set of **8** blocks... and **33** evaluation blocks, which **never
> contributed to the threshold selection**."* ✅

กวาด τ ใน {0.50, …, 0.99} บน 8 block นั้น ได้ **τ\* = 0.75** 〔หน้า 5 บรรทัด ~68
และ หน้า 12 บรรทัด ~42〕

**โมเดลที่เทียบ**

| ชั้น | โมเดล |
|---|---|
| ชั้น 1 — ML | **Random Forest**, XGBoost, LightGBM, CatBoost, Decision Tree |
| ชั้น 1 — DL | **CNN**, RNN, LSTM |
| ชั้น 2 — one-class | **Isolation Forest**, Local Outlier Factor, One-Class SVM |

สถิติที่ใช้ตัดสิน **Friedman test** → **Nemenyi post-hoc** → **Wilcoxon signed-rank
พร้อม Bonferroni correction** → **Cliff delta** วัด effect size

### ได้อะไรออกมา

**1. ML เท่ากับ DL — ไม่มีนัยสำคัญทางสถิติ** 〔หน้า 10 · บรรทัด ~97–102〕

| โมเดล | F1 weighted |
|---|---:|
| CNN (DL ที่ดีที่สุด) | 0.7415 |
| **Random Forest (ML ที่ดีที่สุด)** | **0.7387** |

> *"no statistically significant difference between the ML and DL approaches
> (**Wilcoxon: p = 0.538; Cliff's δ = 0.054, negligible**)"*
> และ Mann-Whitney U test p = 0.229 〔หน้า 11 · บรรทัด ~16〕

**เหตุผลที่เลือก Random Forest** 〔หน้า 10 · บรรทัด ~107〕
> *"Random Forest offers well-established **robustness**, native **feature
> importance estimation**, and substantially **lower computational cost**"*

**2. Isolation Forest ชนะ one-class ตัวอื่นชัด** 〔หน้า 11 บรรทัด ~41 และ หน้า 13 บรรทัด ~51〕

> *"Isolation Forest emerges as the most effective one-class detector
> (**F1 weighted = 0.949 ± 0.028, Friedman rank 1.29, p < 0.001**)"*
> และ accuracy 0.953 ± 0.027, MCC 0.713 ± 0.050

เหตุผลเชิงปฏิบัติที่เขายกให้ 〔หน้า 4 · บรรทัด ~1〕
> *"**linear time complexity**, and **reduced memory requirements**, the Isolation
> Forest has become particularly attractive for industrial monitoring applications
> involving continuous data streams"*

**3. ต่อสองชั้นแล้วดีขึ้นจริง** 〔หน้า 13 · บรรทัด ~57〕

| ตัวชี้วัด | ส่วนต่าง | p |
|---|---:|---|
| F1 weighted | **+9.10 จุด** | < 0.001 |
| Cohen kappa | +0.191 | < 0.001 |
| MCC | +0.168 | < 0.001 |

**routing rate** (สัดส่วนที่ถูกส่งต่อชั้น 2) 〔หน้า 13 · บรรทัด ~22〕
*"exhibited significant variability across experiments"* ตั้งแต่ **1% ถึง 90%**
และสูงที่สุดใน block ที่เป็น fully open-set — สมเหตุสมผล

### 🚩 เทียบกับของเรา

#### ✅ สนับสนุน (5 ข้อ)

**1. สนับสนุนการเลือก Random Forest ของเรา ด้วยเหตุผลคำเดียวกัน**

เราเขียนใน proposal §5.6.1 ว่าเลือก Random Forest เพราะทนทาน ดู feature importance ได้
และคำนวณเบาพอสำหรับ Pi **เขาเลือกด้วยเหตุผลสามข้อเดียวกันเป๊ะ** 〔หน้า 10 บรรทัด ~107〕
และมี Friedman + Wilcoxon + Cliff delta รองรับว่าไม่ได้แพ้ CNN
**นี่คือการอ้างอิงที่ตอบอาจารย์ได้ตรงที่สุดว่าทำไมไม่ใช้ deep learning**

**2. สนับสนุนว่าไม่จำเป็นต้องใช้ deep learning เมื่อสกัด feature ไว้ดีแล้ว**

ซึ่งเป็นสมมติฐานที่สถาปัตยกรรมทั้งหมดของเราตั้งอยู่บนนั้น
(แต่ดูข้อจำกัดของข้ออ้างนี้ในหัวข้อจุดอ่อนข้อ 1 ด้วย)

**3. ✅ ตอบคำถามข้อ 5 ใน README — Isolation Forest คือเป้าหมายที่ถูก**

เราวางลำดับไว้ว่า เกณฑ์สถิติ → Mahalanobis → **Isolation Forest** โดยยังไม่มีอะไรรองรับ
เขาเทียบบน MAFAULDA แล้ว Isolation Forest ชนะ → **ปลายทางที่เราเล็งไว้ถูกแล้ว**

**4. สนับสนุนการแยกเป็นสองชั้นที่ใช้วิธีคนละแบบ**

ตอนที่พบว่า §5.6 ขัดกับ §7.4.4 เราแก้โดยแยกเป็นชั้นที่ 1 (เทรนจากข้อมูลปกติเท่านั้น)
กับชั้นที่ 2 (supervised จำแนกชนิด) **โครงนี้ตรงกับของเขา** ต่างกันแค่ลำดับ

**5. สนับสนุนความระแวงของเราเรื่องตัวเลขสวยเกินจริง**

**เขารายงาน F1w ประมาณ 0.74 บน open-set ไม่ใช่ 99%** และระบุโปรโตคอลกันรั่วไว้ชัด
→ **ยืนยันว่าคำเตือนที่เราเขียนไว้ท้าย `paper/README.md` ถูกต้อง**

#### 🔄 ต้องเปลี่ยนของเรา (2 ข้อ)

**6. 🔥 แผนของเราขาดช่องทาง "ผิดปกติแต่ไม่รู้ว่าอะไร" — ของเขาแก้ไว้แล้ว**

นี่คือสิ่งที่มีค่าที่สุดที่ได้จากงานนี้ ออกแบบของเราตอนนี้มีชั้นที่ 1 บอกว่าผิดปกติ
และชั้นที่ 2 บอกว่าผิดปกติแบบไหน **แต่เราไม่เคยออกแบบว่าจะทำอย่างไรเมื่อชั้นที่ 1
เตือนแล้วชั้นที่ 2 จำแนกไม่ได้** ซึ่งจะเกิดขึ้นแน่นอนที่หน้างาน เพราะเครื่องจักรจริง
มีความเสียหายชนิดที่ MAFAULDA ไม่มี (เช่น BPFI ที่ dataset นี้ไม่มีเลย)

**กลไก confidence routing ด้วย threshold τ ของเขาแก้ปัญหานี้ตรงๆ** ควรเอามาใส่ใน
`docs/data-pipeline-design.md` และ topic `alert`

**7. ชุด feature ของเราขาด skewness และ spectral entropy**

ของเรา 72 ตัว (12 × 6 ช่อง) ของเขา 286 ตัว สองตัวที่เขามีแต่เราไม่มีและ
**คำนวณบน ESP32 ได้ทั้งคู่**

#### ⬜ ตอบไม่ได้ (2 ข้อ)

**8. ❌ ตอบคำถามข้อ 1 (order tracking) ไม่ได้ — เพราะเขาก็ไม่ได้ทำ**

ค้นทั้งฉบับแล้ว **คำว่าความเร็วรอบปรากฏเพียงสามครั้ง** และไม่มี order tracking
หรือ angular resampling เลย `tach` ถูกรวมเข้าไปในเวกเตอร์ feature เฉยๆ
เขายกเรื่องนี้ไว้ใน future work เท่านั้น 〔หน้า 14 · บรรทัด ~12〕
> *"is expected to enhance detection robustness under **varying load and speed
> conditions**"*

**9. 🚩 เขาระบุ sampling rate = 50 kHz** 〔หน้า 6 · บรรทัด ~69〕

ผลกระทบกับงานของเขา **จำกัด** เพราะ band-power ratios และ spectral entropy
คลาด 2.4% แล้วแทบไม่เปลี่ยนค่า **แต่ `dominant frequency` จะคลาด 2.4% อย่างเป็นระบบ**

### ⚠️ จุดอ่อนของงานนี้

**1. 🚩 "CNN" ของเขาไม่ได้กิน raw signal — กินเวกเตอร์ 286 มิติเหมือนกันหมด**

〔หน้า 10 · บรรทัด ~76〕
> *"All three architectures consume the same 286-dimensional standardised feature
> vector used throughout this paper (**not raw signal segments**)"*

**ข้อสรุป "ML เท่ากับ DL" จึงแคบกว่าที่พาดหัวชวนให้คิด** มันพิสูจน์แค่ว่า
*DL บน feature ที่คนสกัดไว้แล้ว* ไม่ชนะ *ML บน feature ชุดเดียวกัน* ซึ่งไม่น่า
แปลกใจเลย ส่วนข้ออ้างที่แรงกว่าในวงการคือ DL บน **raw waveform** เรียน feature
ได้เองดีกว่าคนสกัด — **งานนี้ไม่ได้ทดสอบข้อนั้น**

⚠️ เวลาอ้างอิงในรายงาน **ต้องเขียนให้ตรงว่าเขาเทียบอะไรกับอะไร**

**2. 🚩 ไม่ระบุขนาดหน้าต่างเลย** 〔มีแค่ *"for each signal window"* หน้า 6 บรรทัด ~84〕
→ **ทำซ้ำไม่ได้** และตรวจไม่ได้ว่าหน้าต่างจากไฟล์เดียวกันไปโผล่ทั้ง train และ test
ภายใน block เดียวกันหรือเปล่า ซึ่งคือ leakage ช่องทางที่เราวัดได้ว่ากินถึง 15 จุด

**3. ไม่แจกแจง recall ตามชนิดความเสียหาย** รายงานแต่ F1 weighted กับ macro
เราวัดเองแล้วว่า ball fault ตรวจง่ายกว่า cage fault มาก ตัวเลขรวมจึงกลบเรื่องนี้

**4. ไม่แยกมวลถ่วง 0/6/20/35 g** ซึ่งเป็นกับดักใหญ่ที่สุดของ MAFAULDA

**5. ใช้ hyperparameter ค่าเริ่มต้นของ scikit-learn** 〔หน้า 13 · บรรทัด ~72〕
(เขายอมรับเอง)

**6. calibration set มีแค่ 8 block** (เขายอมรับเอง)

**7. รวมทุกความเสียหายที่ไม่รู้จักเป็นคลาสเดียว** `Unknown Anomaly` ไม่ได้แยกชนิด
— สำหรับงานเราที่ต้องบอกช่างซ่อมว่าให้ไปดูอะไร ข้อนี้สำคัญ

**8. ห้องแล็บล้วน** 〔หน้า 13 บรรทัด ~64 และ หน้า 14 บรรทัด ~15〕 และใช้เซ็นเซอร์ชนิดเดียว

### คำค้นต่อจากฉบับนี้

```
open-set recognition fault diagnosis
confidence threshold rejection classifier
Support Vector Data Description SVDD
Friedman Nemenyi test classifier comparison
Matthews correlation coefficient imbalanced fault
```

**งานที่ควรไล่หาต่อ** ไล่ **reference [19]** ของเขา เรื่อง ML ชนะ DL บนข้อมูล tabular
(น่าจะเป็นงานของ Grinsztajn หรือ Shwartz-Ziv) → ใช้อ้างอิงเรื่องไม่ใช้ DL ได้ตรงกว่า

---

<a id="paper01"></a>

## 01 · A Lightweight Edge Fusion Method

**Jiang, J.** — School of Statistics and Data Science, Hebei Finance University, จีน
*IEEE 6th International Conference on Electronic Technology, Communication and
Information (ICETCI) 2026* · DOI 10.1109/ICETCI68937.2026.11610834 · หน้าวารสาร 292–297

> 🔘 [**📄 เปิดเอกสาร**][pdf01] · ไปหน้า [2 (การแบ่งข้อมูล)][pdf01p2]
> · [3 (ตาราง feature + เหตุผลเลือก RF)][pdf01p3]
> · [**5 (ตารางผลต่อชุดเซ็นเซอร์ + ข้อจำกัด)**][pdf01p5] · [⬆ ดัชนี](#index)

### เขาทำอะไร
เสนอ workflow สำหรับ **สกัด feature บน edge device ที่ทรัพยากรจำกัด**
แล้วรวม feature จากหลายชนิดเซ็นเซอร์ (feature-level fusion)
**นี่คือสถาปัตยกรรมเดียวกับที่เราออกแบบไว้**

### ทำอย่างไร

```
แฟ้มดิบ → ทำความสะอาดช่อง → จัดเรียงให้ตรงเวลา → สร้างหน้าต่าง
       → สกัดสถิติต่อช่อง → ต่อเวกเตอร์เข้าด้วยกัน → Random Forest
```

**9 สถิติต่อช่อง** 〔หน้า 3 · **Table I** บรรทัด ~19〕
mean, std, rms, min, max, ptp, abs_mean, **skew**, kurtosis
→ 8 ช่อง × 9 = **72 feature**

**สำคัญ: ไม่ตัดหน้าต่างเลย** ใช้**หนึ่งไฟล์เป็นหนึ่งตัวอย่าง**
〔หน้า 2–3 · หัวข้อ IV-B〕 แล้วแบ่ง 〔หน้า 3 · บรรทัด ~59〕
> *"The split of MAFAULDA has **1365 training samples and 586 test samples**"*

และกัน leakage ไว้ชัด 〔หน้า 2 · บรรทัด ~92〕
> *"**the same raw recording will not be contained in both training and test sets**,
> thus avoiding the positive bias of close duplicates"* ✅

**เหตุผลที่เลือก Random Forest** 〔หน้า 3 · หัวข้อ IV-E บรรทัด ~48〕
> *"This choice was made intentionally; random forests have **stronger stability in
> structured feature data**, perform well in large amounts of features and are
> **less complex compared to many deep learning models**."*

ข้อมูล 〔หน้า 2 · บรรทัด ~39〕 *"1951 multivariate time series sampled at a rate of
**50kHz** for 5s"* 🚩

### ได้อะไรออกมา

〔หน้า 5 · **Table III** บรรทัด ~9〕

| ชุดเซ็นเซอร์ | feature | accuracy | macro-F1 |
|---|---:|---:|---:|
| **ไมโครโฟนเดียว** | 9 | **0.8174** | 0.6975 |
| overhang 3 ช่อง | 27 | 0.8601 | 0.7786 |
| **underhang 3 ช่อง** | 27 | **0.9727** | 0.9717 |
| สั่นสะเทือน 6 ช่อง | 54 | 0.9795 | 0.9703 |
| **ทุกช่อง (+tach +mic)** | 72 | **0.9898** | 0.9796 |

ข้อสรุปของเขาเรื่อง mic 〔หน้า 5 · บรรทัด ~22〕
> *"the **microphone-only model is significantly inferior** to the vibration-based
> models; therefore, sound signals cannot distinguish between different faults on
> their own."*

(⚠️ แต่ 0.8174 บน 6 คลาส ขณะที่การเดาสุ่มได้ ~0.17 ไม่ใช่ตัวเลขที่ควรเรียกว่าแย่)

### 🚩 กระทบเราอย่างไร

**✅ ยืนยันสถาปัตยกรรมของเราทั้งก้อน** สกัดสถิติง่ายๆ บน edge แล้วส่งเวกเตอร์เล็กๆ
ไปจำแนกด้วย Random Forest — มีงานตีพิมพ์ทำแบบเดียวกันและได้ผลดี
**และเลือก Random Forest ด้วยเหตุผลคำเดียวกับเราอีกครั้ง**

**🔄 ชี้ว่าเราขาด `skew`** ซึ่งคำนวณพร้อม kurtosis ได้แทบฟรี

**🚩 underhang ชนะ overhang ถึง 11 จุด (0.9727 vs 0.8601)** เขาไม่อธิบายว่าทำไม
เราอาจมีคำตอบอยู่แล้ว — เราวัดได้ว่า **`o_radial` อ่อนกว่าช่องอื่นประมาณ 20 เท่า**
ชุด overhang จึงเสียช่องไปหนึ่งช่องจากสามโดยปริยาย
**ถ้าใช่ นี่คือสิ่งที่เรารู้แต่เขาไม่รู้**

### ⚠️ จุดอ่อน
- **ใช้แต่ feature โดเมนเวลา ไม่มีโดเมนความถี่เลย** 〔หน้า 5 · บรรทัด ~50〕
  > *"At present, the **only restricted feature is the time domain**; further
  > enhance it with frequency domain or time-frequency based methods."*
- **เอาช่อง `tach` มาคิดสถิติเป็น feature** → สถิติของ tach เข้ารหัสความเร็วรอบ
  ซึ่งเราพิสูจน์แล้วว่าความเร็วรอบสัมพันธ์กับกลุ่มมวลถ่วง = **leakage อีกช่องทาง**
  (การเพิ่มจาก 0.9795 → 0.9898 มาจากประตูบานนี้)
- **ไม่คุมมวลถ่วง** → คลาส bearing มี imbalance ปน
- 🚩 **อ้างคำว่า "lightweight edge" ตลอดฉบับ แต่ยอมรับเองว่า** 〔หน้า 5 · บรรทัด ~55〕
  > *"this paper has **not yet released device-level runtime/memory/energy data**"*
  → **ไม่เคยวัดบนอุปกรณ์จริงเลย คำถามข้อ 6 ของเรายังเปิดอยู่**

---

<a id="paper06"></a>

## 06 · Cutting-Edge Anomaly Detection (IoT + ML)

**Ūselis, R., Pomarnacki, R. & Serackis, A.** — Vilnius Gediminas Technical
University, ลิทัวเนีย
*IEEE 11th Workshop on Advances in Information, Electronic and Electrical
Engineering (AIEEE) 2024* · DOI 10.1109/AIEEE62837.2024.10586631

> 🔘 [**📄 เปิดเอกสาร**][pdf06] · ไปหน้า [2 (feature + กรอบ 1 วินาที + การแบ่ง)][pdf06p2]
> · [**3 (ตาราง I–IV ลายเซ็นข้ามฝั่ง)**][pdf06p3] · [⬆ ดัชนี](#index)

### เขาทำอะไร
หาว่า **เซ็นเซอร์ตัวเดียวตัวไหนใช้จำแนกความเสียหายได้ดีที่สุด** ภายใต้ข้อจำกัด
ของอุปกรณ์ IoT โดยเน้นว่าสถิติง่ายๆ คำนวณได้เร็วพอสำหรับ real-time บน edge

### ทำอย่างไร
- feature 〔หน้า 2 · บรรทัด ~147〕 mean, median, std, min, max, **skewness**,
  kurtosis, RMS
- **9 คลาส** 〔หน้า 3 · บรรทัด ~16〕 — Normal, Overhang ball/cage/outer,
  H-misalign, V-misalign, Underhang ball/cage/outer → **ไม่มีคลาส imbalance**
- ข้อมูล 〔หน้า 2 · บรรทัด ~80〕 *"each representing a fixed rotation speed ranging
  from **737 RPM to 3686 RPM**, sampled at approximately 60 RPM intervals"*
  (= 12.28–61.4 Hz ตรงกับที่เรานับได้เป๊ะ ✅) และ *"a **50 kHz** sampling rate"* 🚩
- กรอบวิเคราะห์ 〔หน้า 2 · บรรทัด ~86〕
  > *"**a 1-second analysis frame was extracted from each sequence**, selecting
  > non-overlapping frames for further analysis."*
- เครื่องมือ 〔หน้า 2 · หัวข้อ III-B บรรทัด ~96〕 ใช้ **TPOT** (Tree-based Pipeline
  Optimization Tool) ซึ่งเป็น AutoML ด้วย genetic programming
- แบ่ง 〔หน้า 2 · หัวข้อ III-C บรรทัด ~109〕 *"splitting the dataset into a training
  and a test model with a **80:20 ratio**"*

### ได้อะไรออกมา

**เรียงตามช่องเซ็นเซอร์** 〔หน้า 3 · **Table I** บรรทัด ~29〕

| ช่อง | accuracy | F1 | โมเดลที่ดีที่สุด |
|---|---:|---:|---|
| **microphone** | **96.02%** | 95.12% | XGBoost |
| underhang radial | 93.26% | 92.95% | RandomForest |
| underhang axial | 88.05% | 88.47% | GradientBoosting |
| underhang tangential | 75.90% | 78.57% | ExtraTrees |
| overhang radial | 72.39% | 73.44% | XGBoost |
| overhang tangential | 67.27% | 63.97% | RandomForest |
| **overhang axial** | **63.85%** | 58.30% | RandomForest |

**ตารางคลาสที่แต่ละช่องทำได้ดีที่สุด** ← จุดที่น่าตื่นเต้นที่สุด
〔หน้า 3 · **Table II** บรรทัด ~43〕

| ช่อง | คลาสที่ตรวจได้ดีสุด | F1 |
|---|---|---:|
| **overhang axial** | **Underhang-ball fault** | 94.23% |
| overhang radial | Under-outer race | 99.01% |
| overhang tangential | Underhang-ball fault | 93.66% |
| **underhang axial** | **Overhang-ball fault** | **100.00%** |
| underhang radial | Overhang-outer race | 97.58% |
| underhang tangential | Overhang-ball fault | 94.37% |

**คลาสที่แต่ละช่องทำได้แย่ที่สุด** 〔หน้า 3 · **Table III** บรรทัด ~55〕

| ช่อง | คลาสที่แย่สุด | F1 |
|---|---|---:|
| overhang axial | **Normal** | **6.25%** |
| overhang tangential | **Normal** | 9.52% |
| overhang radial | **Normal** | 37.65% |
| underhang tangential | Normal | 69.39% |
| underhang radial | Normal | 85.18% |
| microphone | Normal | 89.72% |

**F1 ต่อคลาสเมื่อใช้ไมโครโฟน** 〔หน้า 3 · **Table IV** บรรทัด ~74〕
Normal 0.897 · OH-ball 0.931 · OH-cage 0.966 · OH-outer 0.934 ·
H-misalign 0.975 · V-misalign 0.982 · UH-ball 0.962 · UH-cage 0.957 · UH-outer 0.956

### 🚩🚩 กระทบเราอย่างไร — ยืนยันข้อค้นพบที่เราอธิบายไม่ได้

**✅ ลายเซ็นข้ามฝั่งมีจริง ไม่ใช่ร่องรอยของรอบบันทึก**

เราเขียนไว้ใน `paper/README.md` เป็นคำถามข้อ 7 ว่า

> เราพบว่า **4 จาก 7 ลายเซ็นอยู่ที่เซ็นเซอร์ฝั่งตรงข้ามกับตลับลูกปืนที่เสีย**
> และยังอธิบายไม่ได้ว่าเป็นการส่งผ่านการสั่นจริง หรือเป็นร่องรอยของรอบบันทึก

และใน `CLAUDE.md` ว่า **"underhang ball → `o_axial` rms 5–12 เท่า"**

**Table II ของเขาบอกว่า `overhang axial` ตรวจ Underhang-ball ได้ดีที่สุด (F1 94.23%)
และ `underhang axial` ตรวจ Overhang-ball ได้ F1 100%**

**คือเรื่องเดียวกันเป๊ะ ทั้งสองทิศ และอยู่บนแกน axial เหมือนกัน**
→ คนละกลุ่มวิจัย คนละวิธี **เจอปรากฏการณ์เดียวกัน** จึงเป็นการส่งผ่านการสั่นจริง

**✅ ยืนยันว่าคลาส Normal แยกยากผิดคาด**

เราวัดได้ว่า *"normal มีระดับพื้นสูงกว่าเกือบทุกคลาสที่เสีย ซึ่งผิดจากสัญชาตญาณ"*
**Table III ของเขาแสดงว่า Normal เป็นคลาสที่แย่ที่สุดของ _ทุกช่อง_ ทั้ง 6 ช่อง**
และต่ำถึง F1 6.25% บน overhang axial → ปรากฏการณ์เดียวกัน

### 🔄 แต่ฉบับนี้ขัดแย้งกับการตัดสินใจของเราหนึ่งเรื่อง

**เขาพบว่า `mic` เป็นช่องที่ดีที่สุด (96.02%) ชนะทุกช่องสั่นสะเทือน**
〔หน้า 3 · บรรทัด ~70〕
> *"Using features extracted from microphone recordings... we were able to achieve
> **the highest overall accuracy and F1-scores across almost all classes, making it
> the most reliable sensor** in this classification task"*

**เราตัดช่อง `mic` ออกตั้งแต่ต้น** เพราะวัดได้ว่าสเกลของ `mic` ในคลาส imbalance
สูงกว่าคลาสอื่น 88 เท่า

**ตรวจแล้วว่าคำอธิบายของเราใช้กับฉบับนี้ไม่ได้** เพราะ**เขาไม่มีคลาส imbalance
ในชุด 9 คลาสของเขา** และในอีก 9 คลาสที่เหลือ สเกลของ mic ที่เราวัดอยู่ที่
1.003–1.252 เท่า คือต่างกันแค่ 1.25 เท่า ไม่ใช่กับดักสเกล

> 🔄 **ต้องยอมรับว่าการตัด `mic` ออกทั้งช่องของเราอาจเป็นการตัดสินใจที่ผิด**
> กับดัก 88 เท่าที่เราเจอมีจริงแต่**จำกัดอยู่ที่คลาส imbalance เท่านั้น**
> **ทางที่ถูกคือ normalize ต่อไฟล์แล้วเอา `mic` กลับมา ไม่ใช่ตัดทิ้ง**
> (ซึ่งเป็นทางเลือกที่ 1 ที่เราเขียนไว้ใน `CLAUDE.md` เองแต่ไม่ได้เลือก)
>
> ฉบับ 01 ได้ mic เดี่ยว 0.8174 ด้วย ซึ่งก็สูงเกินจะมองข้าม

### ⚠️ จุดอ่อน
- **ข้อความเรื่องการแบ่งคลุมเครือ** *"a 1-second analysis frame was extracted from
  each sequence"* (เอกพจน์) อ่านได้ว่า **หนึ่งไฟล์ให้หนึ่งกรอบ** ซึ่งถ้าใช่
  การแบ่ง 80:20 จะเท่ากับแบ่งตามไฟล์และ**ไม่รั่ว** แต่คำว่า *"selecting
  non-overlapping frames"* (พหูพจน์) เปิดช่องให้ตีความว่าเอาหลายกรอบต่อไฟล์
  **ตัดสินจากเอกสารไม่ได้** — ข้อนี้สำคัญเพราะมันตัดสินว่าตัวเลข 96% เชื่อได้แค่ไหน
- **ใช้ TPOT ซึ่งเป็น AutoML** ไล่ลองไปป์ไลน์จำนวนมากบนข้อมูลชุดเล็ก
  เป็นความเสี่ยง overfitting ในตัวมันเอง และทำให้ตัวเลข accuracy มีอคติขึ้นได้
- **ลำดับช่องของเขาขัดกับฉบับ 10** → ดูหัวข้อ "สิ่งที่วรรณกรรมยังไม่ลงรอยกัน"

---

# ส่วนที่ 2 — ฉบับรองที่ยังมีประโยชน์

<a id="paper11"></a>

## 11 · The Influence of Handling Imbalance Classes

**Ali, M. A., Bingamil, A. A., Jarndal, A. & Alsyouf, I.** — University of Sharjah, UAE
*8th International Conference on Modeling Simulation and Applied Optimization
(ICMSAO) 2019*

> 🔘 [**📄 เปิดเอกสาร**][pdf11] · ไปหน้า [1][pdf11p1]
> · [**2 (รายการ 25 feature + ความถี่การหมุน)**][pdf11p2] · [3 (SMOTE)][pdf11p3]
> · [4 (ตารางผล 81.2 → 96.2)][pdf11p4] · [⬆ ดัชนี](#index)

เป็นฉบับที่งานอื่นอ้างถึงบ่อย (ตัวเลข 96.2% ที่ฉบับ 10 ยกมาเทียบใน Table VII)

**ทำอะไร** สร้างตัวจำแนกที่ใช้ feature **น้อยที่สุด** เพื่อลดต้นทุนการคำนวณ

**ทำอย่างไร** ใช้เพียง **25 feature** 〔หน้า 2 · หัวข้อ III-A บรรทัด ~54–85〕

- **ความถี่การหมุน `Fr`** — *"Discrete Fourier Transform (DFT) was applied on the
  tachometer signal to estimate the final Rotation frequency Rf"*
- **mean, entropy, kurtosis** ของทั้ง 8 ช่อง — entropy หาด้วย
  *"**Parsen-Rosenblatt window method** on all 8 vibration signals"* 〔บรรทัด ~64〕
- > *"hence, using **only 25 features** to describe the complete machine setup,
  > which is smaller than the implemented 31 features in [2]"* 〔บรรทัด ~85〕
- จัดการคลาสไม่สมดุลด้วย **SMOTE** 〔หน้า 3 · หัวข้อ III-B บรรทัด ~20〕
  แล้วจำแนกด้วย MLP (1 hidden layer, 10 neurons)

**ได้อะไร** 〔หน้า 4 · **Table I และ Table II** บรรทัด ~24 และ ~43〕

| | accuracy |
|---|---:|
| ไม่ใช้ SMOTE | **81.2%** |
| **ใช้ SMOTE** | **96.2%** |

> *"The overall systems accuracy increases from **81.2% to 96.2%**, achieving a
> relative increase of about 15% in predictive..."* 〔หน้า 4 · บรรทัด ~43〕

### 🚩 กระทบเราอย่างไร
**✅ ยืนยันการตัดสินใจส่งความเร็วรอบไปพร้อม feature ทุกครั้ง**
เราออกแบบไว้ใน `src/service/schema.py` ให้ทุกข้อความมี `rot_hz`
งานนี้**ใช้ความถี่การหมุนเป็น feature ตัวแรกเลย** และ**เป็นงานเดียวจาก 11 ฉบับที่ทำ**

**🔄 `entropy` โผล่มาเป็นฉบับที่ 3** (ฉบับ 02 และ 06 ก็มี) เราไม่มี → **ควรเพิ่ม**

**⚠️ สัญญาณเตือนสองข้อ** ใช้เพียง 25 feature ได้ 96.2% และ **SMOTE ทำให้เพิ่ม 15 จุด**
ซึ่งเป็นตัวเลขเดียวกับที่ฉบับ 04 ได้ (ดูข้างล่าง) และ**ไม่ระบุว่าทำ SMOTE
ก่อนหรือหลังแบ่ง train/test**

---

<a id="paper04"></a>

## 04 · Classification Using SMOTE and Deep Neural Networks

**Bingamil, A. A. et al.** — *IECON 2022, 48th Annual Conference of the IEEE
Industrial Electronics Society* · DOI 10.1109/IECON49645.2022.9968875
(กลุ่มเดียวกับฉบับ 11)

> 🔘 [**📄 เปิดเอกสาร**][pdf04] · ไปหน้า [**3 (จุดที่ SMOTE ทำก่อนแบ่ง)**][pdf04p3]
> · [5 (ผล 82 → 97)][pdf04p5] · [⬆ ดัชนี](#index)

**ทำอะไร** ต่อยอดจากฉบับ 11 โดยเพิ่ม **relief feature selection** เพื่อคัด feature
ที่สำคัญที่สุด แล้วเทียบ MLP กับ LSTM

**ทำอย่างไร** สกัด feature → **SMOTE** → relief คัด feature → scale 0–1 →
แบ่ง 〔หน้า 3 · บรรทัด ~36〕
> *"The data were **divided into training 70% and testing 30% sets using stratified
> splitting**"*

**ได้อะไร** 〔หน้า 5 · บรรทัด ~16〕
> *"The total accuracy of the system improves **from 78,9% to 90% for the LSTM**
> classifier and **from 82% to 97% for the MLP** classifier."*

### 🚩🚩 กระทบเราอย่างไร — ตัวอย่างกับดักที่เราควรเขียนไว้ในรายงาน

〔หน้า 3 · หัวข้อ V-B บรรทัด ~60–64〕
> *"it is necessary to distribute the data equally by **resampling the whole
> dataset**. To resolve this problem... the **SMOTE is applied to resample the
> dataset**."*

และการจูน hyperparameter 〔หน้า 3 · บรรทัด ~53〕
> *"selected using the k-fold cross-validation procedure on the **expanded
> database**"*

> **อ่านรวมกันแล้วแปลว่า SMOTE ถูกทำ _ก่อน_ แบ่ง train/test**
>
> SMOTE สร้างตัวอย่างสังเคราะห์ด้วยการ**ลากเส้นระหว่างตัวอย่างจริงที่อยู่ใกล้กัน**
> (สมการ (10) ของเขา `D_syn = Dᵢ + (D_KNN − Dᵢ)·r` 〔หน้า 3〕)
> ถ้าทำก่อนแบ่ง ตัวอย่างในชุดทดสอบจะเป็น**ส่วนผสมเชิงเส้นของตัวอย่างในชุดเทรน**
> → รั่วโดยตรง
>
> **การที่ accuracy พุ่งจาก 82% → 97% เพราะใส่ SMOTE จึงน่าจะเป็นขนาดของการรั่ว
> ไม่ใช่ขนาดของการพัฒนา** 15 จุด ซึ่งอยู่ในระดับเดียวกับ 15 จุดที่เราวัดได้
> จากการเปลี่ยน random-window เป็น by-file (0.996 → 0.843)
>
> และ**ฉบับ 11 จากกลุ่มเดียวกันได้ +15 จุดจาก SMOTE เหมือนกันเป๊ะ** (81.2 → 96.2)
> ซึ่งชี้ว่าเป็นแบบแผนเดียวกันทั้งสองฉบับ

**บทเรียนสำหรับเรา** ถ้าเราใช้ SMOTE หรือ oversampling ใดๆ **ต้องทำหลังแบ่งแล้ว
และทำกับชุดเทรนเท่านั้น** นี่เป็นกับดัก leakage คนละช่องทางกับที่เราเคยวัด
และควรเพิ่มเข้ารายการกับดักใน `CLAUDE.md`

---

<a id="paper09"></a>

## 09 · Fault Diagnosis Using Hybrid Models

**Al Maruf, A., Sajib, S. Z., Rawnak, A. & Shiblee, M. S. A. A. F.**
Military Institute of Science and Technology, Dhaka, บังกลาเทศ
*IEEE 2nd International Conference on Computing, Applications and Systems
(COMPAS) 2025* · DOI 10.1109/COMPAS67506.2025.11381784

> 🔘 [**📄 เปิดเอกสาร**][pdf09] · ไปหน้า [**2 (ภาพที่ระบุ Overhang Bearing 0g)**][pdf09p2]
> · [3 (การแบ่ง 80-20)][pdf09p3] · [5 (ผล DNN 95%)][pdf09p5] · [⬆ ดัชนี](#index)

**ทำอะไร** เทียบโมเดลพื้นฐาน 6 ตัวบน MAFAULDA — Logistic Regression, SVM,
Naïve Bayes, kNN, Decision Tree, DNN

**ทำอย่างไร** 〔หน้า 2 · หัวข้อ III-B〕 downsample สัญญาณดิบเพื่อลดขนาด → FFT →
สกัด feature → แบ่ง 〔หน้า 3 · บรรทัด ~25 และ ~33〕 *"The dataset was **split 80-20**
for training and testing"*

**ได้อะไร** 〔หน้า 5 · บรรทัด ~12〕
> *"the Deep Neural Network (DNN)... outperforms all other models, achieving a
> **test accuracy of 95%**"*

### กระทบเราอย่างไร
**🟡 ประโยชน์จำกัด** เป็นงานเทียบโมเดลมาตรฐานที่ไม่มีอะไรใหม่เชิงวิธีการ
และแบ่ง 80/20 โดยไม่ระบุการจัดกลุ่ม

**แต่มีจุดที่น่าสังเกต** ชื่อภาพของเขาระบุว่า *"Raw Time-domain Signal for
**Overhang Bearing 0g**"* 〔หน้า 2 · Fig. 1, Fig. 2 และ Fig. 3 บรรทัด ~71–90〕
→ **เป็นฉบับเดียวจาก 10 ฉบับที่แสดงว่ารู้เรื่องชั้นมวลถ่วง** แม้จะไม่ได้ใช้
ควบคุมการทดลอง ส่วนฉบับอื่นไม่เอ่ยถึงเลย

**→ กับดัก "imbalance ปนใน bearing fault" ที่ `CLAUDE.md` เตือนไว้
แทบไม่มีใครในวรรณกรรมชุดนี้จัดการเลย** เป็นช่องที่งานเราทำได้ดีกว่า

---

<a id="paper07"></a>

## 07 · Denoising Induction Motor Sounds Using an Autoencoder

**Tran, T., Bader, S. & Lundgren, J.** — STC Research Centre, Mid Sweden University
*IEEE Sensors Applications Symposium (SAS) 2023* · DOI 10.1109/SAS58821.2023.10254150

> 🔘 [**📄 เปิดเอกสาร**][pdf07] · ไปหน้า [1][pdf07p1]
> · [**2 ⭐ (จุดที่เขียน 51 200 Hz และ 50 000 Hz ขัดกันในหน้าเดียว)**][pdf07p2]
> · [⬆ ดัชนี](#index)

**ทำอะไร** ลบสัญญาณรบกวนออกจาก**เสียง**มอเตอร์ด้วย autoencoder เพื่อให้เอาไป
จำแนกต่อได้ดีขึ้น ลบสองชนิดคือ Gaussian white noise และเสียงน้ำไหล

**ทำอย่างไร** ป้อนคู่ (เสียงที่เติม noise, เสียงสะอาด) ให้ autoencoder เรียน
ใช้ **246 เสียง** 〔หน้า 1 · Abstract บรรทัด ~15〕 คือ 〔หน้า 2 · บรรทัด ~55〕
*"There are **49 sounds** in the normal function category... There are **197 sounds**
in the horizontal misalignment category, divided into four types: 0.5mm (50 sounds),
1.0mm (49), 1.5mm (49), and 2.0mm (49)"*

**ตรงกับจำนวนที่เรานับได้เป๊ะทุกตัว ✅** (49 + 197 = 246)

**ได้อะไร** MSE ≤ 0.15 ทั้งสองชนิดของ noise

### 🚩 กระทบเราอย่างไร — มีจุดเดียวแต่สำคัญมาก

**ฉบับนี้เป็นฉบับเดียวจาก 11 ฉบับที่เอ่ยถึงเลข 51,200 Hz**

〔หน้า 2 · หัวข้อ II Dataset บรรทัด ~47〕
> *"two National Instruments NI 9234 4 channel analog acquisition modules
> **with a sample rate of 51 200 Hz**."*

แล้ว **18 บรรทัดถัดมาในหน้าเดียวกัน** 〔หน้า 2 · บรรทัด ~65〕
> *"Each signal was **sampled at a rate of 50 000 Hz** for 5 seconds, resulting in
> time series of 250 000 samples."*

> **เขาเขียนทั้งสองค่าไว้ในหน้าเดียวกันโดยไม่สังเกตว่ามันขัดกัน**
> และนี่คือ**หลักฐานที่ตรงที่สุดว่าข้อค้นพบของเรามีค่า** เพราะเหตุผลที่เราใช้
> ยืนยัน 51,200 Hz คือ *"51.2 kHz คือ sampling rate สูงสุดของ NI 9234"*
> ซึ่ง**เป็นประโยคเดียวกับที่เขาเขียน** แต่เขาไม่ได้เอามาปะติดปะต่อกับ
> เลข 250,000 แถว และ 5 วินาที
>
> **เรายังเป็นฝ่ายเดียวที่สรุปได้ว่าอัตราการสุ่มของข้อมูลคือ 51,200 Hz**
> และทำด้วยการวัดจาก tachometer เทียบชื่อไฟล์ 1,718 ไฟล์
> (ดู `experiments/2026-09-20-sampling-rate.md`)

**ของที่อาจใช้ได้ต่อ** autoencoder เป็นวิธีมาตรฐานสำหรับ anomaly detection
ที่เทรนจากข้อมูลปกติเท่านั้น (ดู reconstruction error) — เป็นทางเลือกที่ 4
ต่อจาก Isolation Forest ในชั้นที่ 1 ของเรา แต่หนักกว่าและอธิบายยากกว่า

---

<a id="paper03"></a>

## 03 · Analysis of Almost-periods of Vibration Signals

**Avkhimenko, G. M.** — Laboratory №46, Institute of Control Sciences RAS, มอสโก
*16th International Conference Management of Large-Scale System Development
(MLSD) 2023* · DOI 10.1109/MLSD58227.2023.10304002

> 🔘 [**📄 เปิดเอกสาร**][pdf03] · ไปหน้า [1 (รายการเซ็นเซอร์)][pdf03p1]
> · [2 (ใช้ 3 สัญญาณ)][pdf03p2] · [5 (บทสรุปที่ยอมรับว่าทำอัตโนมัติไม่ได้)][pdf03p5]
> · [⬆ ดัชนี](#index)

**ทำอะไร** งานคณิตศาสตร์ล้วน นิยาม "almost-period" (คาบที่เกือบซ้ำ แต่ไม่ซ้ำเป๊ะ)
และหามันด้วยวิธี **shift function** โดยดูตำแหน่งต่ำสุดเฉพาะที่ของกราฟ

**ทำอย่างไร** 〔หน้า 2 · บรรทัด ~53〕
> *"**One signal for each fault was selected** for analysis, respectively."*

คือใช้ **สัญญาณเดียวต่อหนึ่งความเสียหาย รวม 3 สัญญาณ** แล้ววิเคราะห์หาคาบด้วยมือ
(ระบุรายการเซ็นเซอร์ไว้ครบรวม Monarch MT-190 tachometer 〔หน้า 1 บรรทัด ~106〕
และบอกว่าใช้ 49 ความเร็วรอบ 〔หน้า 1 บรรทัด ~117〕 ซึ่งตรงกับชุด normal ของเรา)

**ได้อะไร** ได้ชุดคาบของแต่ละสภาวะ และเสนอว่าเอาไปใช้เป็น feature ได้
(เรียงคาบจากน้อยไปมากเป็นเวกเตอร์)

### กระทบเราอย่างไร
**⬜ แทบไม่มีประโยชน์กับงานเราตอนนี้** ไม่มีการจำแนก ไม่มี accuracy
ใช้แค่ 3 สัญญาณ และ**เขายอมรับเองว่าทำอัตโนมัติไม่ได้** 〔หน้า 5 · บทสรุป บรรทัด ~33〕

> *"But the search of almost-periods by the method of shift functions has the
> following disadvantage. **It is difficult to automate the analysis process**,
> i.e. to reduce it to a step-by-step algorithm. Since the search for almost-periods
> consists of analyzing local minima of the shift function."*

ซึ่งขัดกับข้อกำหนดของเราว่าต้องรันอัตโนมัติบน edge

**สิ่งเดียวที่ควรจำ** แนวคิดที่ว่าสัญญาณเครื่องจักรมีคาบที่ "เกือบซ้ำ" ไม่ใช่ซ้ำเป๊ะ
เป็นเหตุผลเชิงทฤษฎีที่หนุนว่าทำไม order tracking (ฉบับ 08) จึงช่วย —
เพราะมันทำให้คาบที่เกือบซ้ำกลายเป็นซ้ำเป๊ะในโดเมนมุม

---

# ส่วนที่ 3 — สิ่งที่เห็นได้เฉพาะเมื่ออ่านหลายฉบับรวมกัน

## 🚩 ตารางที่สำคัญที่สุดของเอกสารนี้ — accuracy เทียบกับวิธีแบ่งข้อมูล

**คอลัมน์ 🔗 กดได้ — เปิด PDF ตรงหน้าที่ตัวเลขนั้นอยู่**

| ฉบับ | accuracy | 🔗 ที่มา | ตัดหน้าต่าง? | จัดกลุ่มตามไฟล์ตอนแบ่ง? |
|---|---:|---|---|---|
| 05 Carvalho | **99.11%** | [น.4 Table III][pdf05p4] | ✅ 1,000 แถว + ซ้อน 50% | ❌ **ไม่ระบุเลย** [(น.3)][pdf05p3] |
| 01 Jiang | **98.98%** | [น.5 Table III][pdf01p5] | ❌ ใช้ไฟล์เป็นตัวอย่าง | ✅ **ระบุชัด** [(น.2)][pdf01p2] |
| 10 Kim | **98.51%** | [น.3 Table VI][pdf10p3] | ✅ 10 หน้าต่าง/ไฟล์ | ✅ **ระบุชัด** [(น.2)][pdf10p2] |
| 04 Bingamil | **97.00%** | [น.5][pdf04p5] | — | ⚠️ **SMOTE ก่อนแบ่ง** [(น.3)][pdf04p3] |
| 11 Ali | **96.20%** | [น.4 Table II][pdf11p4] | — | ❌ ไม่ระบุ |
| 06 Ūselis | **96.02%** | [น.3 Table I][pdf06p3] | ✅ กรอบ 1 วินาที | 🟡 **คลุมเครือ** [(น.2)][pdf06p2] |
| 09 Al Maruf | **95.00%** | [น.5][pdf09p5] | ✅ downsample | ❌ ไม่ระบุ [(น.3)][pdf09p3] |
| 02 Costa | **73.87%** | [น.10][pdf02p10] | ✅ (ไม่ระบุขนาด) | 🟡 แยก block แต่ไม่ระบุในระดับไฟล์ [(น.5)][pdf02p5] |
| **ของเรา `by-file`** | **84.30%** | [`experiments/2026-09-25-split-leakage.md`](../experiments/2026-09-25-split-leakage.md) | ✅ 32,768 แถว | ✅ **ระบุชัด + คุมมวล + คุมความเร็ว** |
| **ของเรา `by-speed`** | **72.60%** | [เดียวกัน](../experiments/2026-09-25-split-leakage.md) | ✅ | ✅ **เข้มงวดที่สุด** |

**สามข้อสังเกตที่ควรเขียนลงรายงาน**

1. **ฉบับเดียวที่รายงานตัวเลขต่ำกว่า 95% คือฉบับที่ออกแบบการประเมินเข้มงวดที่สุด**
   (Costa ใช้ open-set 33 block ได้ 0.7387) → **ตัวเลขต่ำไม่ได้แปลว่างานแย่
   มันแปลว่าวัดอย่างซื่อสัตย์**
2. **ตัวเลขของเรา 0.843 อยู่กลางตาราง ไม่ใช่ท้ายตาราง** และได้มาภายใต้เงื่อนไข
   ที่เข้มกว่าทุกฉบับ (bearing เฉพาะ 0 g + คุมช่วงความเร็ว 13.1–61.2 Hz)
   → **ไม่ต้องอายตัวเลขนี้ ต้องอธิบายเงื่อนไขให้ชัด**
3. **ฉบับที่ได้ตัวเลขสูงสุดคือฉบับที่ไม่ระบุวิธีแบ่ง** ซึ่งเป็นแบบแผนที่
   `src/models/leakage_demo.py` ของเราทำนายไว้

## 🚩 เรื่อง sampling rate — นับจาก 11 ฉบับ

| ค่าที่ระบุ | จำนวน | 🔗 ฉบับ · ที่มา (กดได้) |
|---|---:|---|
| **50 kHz (ผิด)** | **8** | [01 น.2][pdf01p2] · [02 น.6][pdf02p6] · [04][pdf04] · [05 น.3][pdf05p3] · [06 น.2][pdf06p2] · [07 น.2][pdf07p2] · [10 น.2][pdf10p2] · [11][pdf11] |
| 51,200 Hz สำหรับ**ตัวโมดูล NI 9234** | **1** | [**07 น.2**][pdf07p2] — แต่ยังเขียนว่าข้อมูลเป็น 50 kHz ในหน้าเดียวกัน |
| ไม่ระบุ | 2 | [03][pdf03] · [08][pdf08] |

**ไม่มีฉบับใดระบุว่าอัตราการสุ่มของ _ข้อมูล_ คือ 51,200 Hz**
และฉบับ 07 เขียนทั้งสองค่าไว้ในหน้าเดียวกันโดยไม่สังเกตความขัดแย้ง

→ **ข้อค้นพบของเรายังเป็นของใหม่** และตอนนี้มีหลักฐานหนักแน่นกว่าเดิมว่าควรรายงาน
เพราะถ้า 8 ฉบับใช้ค่าผิด แกนความถี่ของกราฟในงานเหล่านั้น**คลาดไป 2.4% ทั้งหมด**

## ⚠️ สิ่งที่วรรณกรรมยังไม่ลงรอยกัน — ลำดับของช่องเซ็นเซอร์

| ลำดับ | ฉบับ 10 (ResNet + ภาพ, 7 คลาส มี imbalance) | ฉบับ 06 (tree + สถิติ, 9 คลาส ไม่มี imbalance) |
|---|---|---|
| ดีที่สุด | **tangential** 72.19% | **microphone** 96.02% |
| | axial 64.17% | underhang **radial** 93.26% |
| แย่ที่สุด | **radial** 58.36% | overhang **axial** 63.85% |

**สองฉบับให้ลำดับที่ขัดกัน** ฉบับ 10 บอก radial แย่ที่สุด ฉบับ 06 บอก
underhang radial ดีเป็นอันดับสอง

**คำอธิบายที่น่าจะเป็นไปได้ และเรามีข้อมูลยืนยันอยู่แล้ว**
ฉบับ 10 **เฉลี่ยรวมทั้งสองฝั่ง** (Table II ไม่แยก inner/outer)
ขณะที่ฉบับ 06 **แยกฝั่ง** และเราวัดได้ว่า `o_radial` อ่อนกว่าช่องอื่นถึง 20 เท่า

→ ถ้าเฉลี่ย `u_radial` (ดี) กับ `o_radial` (อ่อนมาก) เข้าด้วยกัน ค่าเฉลี่ยจะดูแย่
**ซึ่งอธิบายได้ว่าทำไมฉบับ 10 จึงได้ radial แย่ที่สุด**
และตารางของฉบับ 06 ก็หนุนคำอธิบายนี้ เพราะ overhang radial (72.39%) ต่ำกว่า
underhang radial (93.26%) ถึง 21 จุด

> **นี่คือตัวอย่างที่ดีที่สุดว่าทำไมงานที่เราทำมาไม่สูญเปล่า**
> เราอธิบายความขัดแย้งระหว่างงานตีพิมพ์สองฉบับได้ ด้วยการวัดที่เราทำเอง
> และ**เป็นข้อสังเกตที่ควรเขียนลงรายงานสหกิจ**

## 🔍 มีใครสกัด "ลายเซ็นของแต่ละคลาส" ได้ไหม — ตรวจทั้ง 11 ฉบับแล้ว

คำถามนี้ตรงกับงานที่เราทำใน `src/features/screen_signatures.py` คือหาว่า
**ความผิดปกติแต่ละชนิดแสดงตัวที่ช่องไหน ด้วยปริมาณอะไร**
(ตารางลายเซ็น 8 คลาสใน `CLAUDE.md` หัวข้อ 5)

**คำตอบสั้น: ไม่มีฉบับไหนทำแบบที่เราทำ** แต่มีฉบับที่ใกล้เคียงและใช้อ้างอิงได้

| ฉบับ | ทำอะไรที่ใกล้เคียง | ใช้แทนตารางลายเซ็นได้ไหม |
|---|---|---|
| **06 Ūselis** | **ตาราง per-sensor × per-class F1** | 🟢 **ใกล้ที่สุด** ดูด้านล่าง |
| **08 Sanami** | สกัดพารามิเตอร์ฟิสิกส์ที่ตีความได้ | 🟡 แนวคิดตรง แต่ไม่มีตัวเลข |
| 02 Costa | **อ้าง** feature importance ของ RF | 🔴 ไม่ได้รายงานเลย |
| 04 Bingamil | **ใช้ Relief feature selection** | 🔴 ไม่ได้รายงานว่าเลือกอะไร |
| 10 Kim | accuracy ต่อแกนเซ็นเซอร์ | 🔴 เฉลี่ยรวมทุกคลาส ไม่แยกคลาส |
| 09, 11 | confusion matrix | 🔴 ได้ recall ต่อคลาส ไม่ใช่ลายเซ็น |
| 01, 03, 05, 07 | — | 🔴 ไม่มี |

### 🟢 ฉบับ 06 คือฉบับเดียวที่ให้ตารางคลาส × ช่องเซ็นเซอร์

〔หน้า 3 · Table II และ Table III〕 — [เปิดดู][pdf06p3]

เขาไม่ได้เรียกมันว่า "ลายเซ็น" แต่ผลที่ออกมาคือแผนที่ว่า **ช่องไหนตรวจคลาสไหนได้ดี
และคลาสไหนไม่ได้เลย** ซึ่งเป็นสิ่งเดียวกันในทางปฏิบัติ

**แต่ต่างจากของเราสองข้อที่สำคัญ**

| | ของเขา | ของเรา |
|---|---|---|
| ละเอียดระดับ | **ช่องเซ็นเซอร์** (6 ช่อง) | **ช่อง × ปริมาณ** (6 × 11 = 66 แบบ) |
| วัดจาก | **ผลของตัวจำแนก** (F1 ของ classifier) | **ค่าที่วัดได้โดยตรง** (AUC ของ feature เดี่ยว) |

ของเขาตอบได้ว่า *"ใช้ช่อง `u_axial` แล้วตรวจ overhang ball ได้"*
ของเราตอบได้ว่า *"overhang ball ทำให้ `o_radial` ถูกครอบด้วยคลื่น ~9.93× ความเร็วรอบ"*
→ **ของเราบอกกลไก ของเขาบอกแต่ผล** ซึ่งต่างกันมากตอนต้องอธิบายให้ช่างซ่อมฟัง
หรือย้ายไปเครื่องจักรจริงที่ไม่มี label ให้เทรน

### 🟡 ฉบับ 08 มีแนวคิดที่ตรงที่สุด แต่ไม่มีตัวเลข

[เปิดดู][pdf08p1] เขาสกัด **damping `c(ω)` และ stiffness `k(ω)`** ซึ่งเป็น
พารามิเตอร์ทางฟิสิกส์จริง แล้วบอกว่า *"The learned parameters exhibit clear trends
with speed and fault condition"*

**นี่คือการสกัดลายเซ็นในความหมายที่แท้จริงที่สุดในบรรดา 11 ฉบับ** เพราะได้ปริมาณ
ที่ตีความทางฟิสิกส์ได้ ไม่ใช่แค่สถิติ **แต่ใช้แค่ 3 คลาส** (normal + misalignment
สองแบบ) และ**เป็นบทคัดย่อ 1 หน้าที่ไม่รายงานตัวเลขเลย** จึงอ้างอิงเป็นแนวทางได้
แต่เทียบตัวเลขไม่ได้

### 🔴 สองฉบับที่บอกว่าทำได้ แต่ไม่ได้ทำ — น่าเสียดายที่สุด

**ฉบับ 02 Costa** อ้างเหตุผลเรื่อง feature importance **สองครั้ง**
〔หน้า 3 บรรทัด ~58〕 และ 〔หน้า 10 บรรทัด ~107〕 ว่าเลือก Random Forest เพราะ
*"native **feature importance** estimation"* และ *"aids in the **post-hoc
interpretation** of the diagnostic"* — **แต่ค้นทั้ง 16 หน้าแล้วไม่มีค่า importance
แม้แต่ตัวเดียว ไม่มีตาราง ไม่มีกราฟ**

**ฉบับ 04 Bingamil** ใช้ **Relief feature selection** เป็นจุดขายถึงขั้นเขียนไว้ใน
บทคัดย่อว่า *"to identify the most affecting features"* และมีหัวข้อย่อย IV-D
อธิบายวิธี Relief เต็มหน้า 〔หน้า 4 บรรทัด ~30〕 — **แต่ไม่เคยบอกว่า Relief
เลือก feature ตัวไหนออกมา** Table 1–4 ของเขาเป็น confusion matrix ล้วน

> **ทั้งสองฉบับมีเครื่องมือที่สกัดลายเซ็นได้อยู่ในมือ แต่ใช้มันเพื่อดัน accuracy
> แล้วไม่รายงานสิ่งที่เครื่องมือบอก** ซึ่งเป็นแบบแผนที่เห็นได้ทั่วไปในวรรณกรรมชุดนี้

### 🚨 และไม่มีฉบับไหนใช้ความถี่ความเสียหายของตลับลูกปืนเลย

ค้นคำ `BPFO` `BPFI` `BSF` `FTF` `envelope` `Hilbert` `characteristic frequency`
`sideband` ทั้ง 11 ฉบับแล้ว **ไม่มีฉบับใดใช้เลย**

สองจุดที่ดูเหมือนจะมี ตรวจแล้วเป็น false positive ทั้งคู่

- ฉบับ 04 มีคำว่า *"envelope... Hilbert Transform"* 〔หน้า 1 บรรทัด ~57〕
  แต่อยู่ใน**หัวข้อ related work ที่เล่าถึงงานของคนอื่น** (reference [9]) ไม่ใช่สิ่งที่เขาทำ
- ฉบับ 09 มีคำว่า `1X` 〔หน้า 2〕 แต่เป็น**เศษจากสูตรคณิตศาสตร์** `b−1X j=0`
  (เครื่องหมายผลรวม) ที่สกัดข้อความออกมาเพี้ยน ไม่ใช่ฮาร์มอนิกที่ 1×

**ทั้ง 11 ฉบับใช้แต่สถิติทั่วไป** (mean, std, rms, kurtosis, skewness, entropy)
กับการแปลงทั้งก้อน (FFT, wavelet, signal-to-image) **ไม่มีใครเจาะไปที่
ความถี่ที่ทฤษฎีบอกว่าควรมี**

### 🚩 สรุปสำหรับรายงานสหกิจ

**ตารางลายเซ็น 8 คลาสของเราเป็นของที่วรรณกรรมชุดนี้ไม่มี** และควรเป็นหัวข้อหนึ่ง
ในรายงาน โดยเฉพาะข้อค้นพบว่า

- **ความถี่ BPFO/BSF/FTF ไม่เคยเป็นพีคเด่นใน dataset นี้เลย** (ตรวจ 51 ไฟล์)
  ซึ่งอธิบายได้ว่า**ทำไมไม่มีใครในวรรณกรรมใช้มัน** — แต่ไม่มีใครเขียนเหตุผลไว้
- **BPFO ทับฮาร์มอนิกที่ 3 ของความเร็วรอบจนแยกไม่ออกเชิงฟิสิกส์**
  (ระยะห่าง 0.06 Hz เทียบกับความละเอียด 0.2048 Hz)
- **4 จาก 7 ลายเซ็นอยู่คนละฝั่งกับความเสียหาย** ซึ่งฉบับ 06 ยืนยันโดยอิสระ

⚠️ **ข้อควรระวังในการเคลม** การที่วรรณกรรมชุดนี้ไม่มีตารางลายเซ็น **ไม่ได้แปลว่า
วงการไม่รู้** ตารางลายเซ็นมาตรฐาน (1× = imbalance, 2× = misalignment, BPFO = รางนอก)
เป็นเนื้อหาระดับตำราและมาตรฐาน ISO ซึ่งงานวิจัยมักข้ามไปเพราะถือว่ารู้กันแล้ว
**สิ่งที่เป็นของใหม่จริงๆ ของเราคือการวัดว่าลายเซ็นตามตำราอันไหน _ใช้ไม่ได้_
กับ dataset นี้ และเพราะอะไร** ไม่ใช่การค้นพบลายเซ็นเอง
→ ยังควรหามาตรฐาน ISO 10816 / ISO 20816 มาอ้างอิงเป็นฐาน

### 📌 lead ใหม่ที่ควรตามต่อ

**reference [9] ของฉบับ 04** เป็นงานเดียวที่โผล่มาในวรรณกรรมชุดนี้ว่าใช้
envelope + Hilbert จริง

> Laala, W., Guedidi, A. & Guettaf, A. (2020). "Bearing faults classification based
> on wavelet transform and artificial neural network." *International Journal of
> System Assurance Engineering and Management.*
> DOI [10.1007/s13198-020-01039-x](https://doi.org/10.1007/s13198-020-01039-x)

น่าจะช่วยเรื่อง **คำถามข้อ 4** (การเลือกย่านความถี่สำหรับ envelope) ได้ด้วย

---

## ✅ สิ่งที่วรรณกรรมเห็นพ้องกัน

| เรื่อง | จำนวนฉบับที่หนุน |
|---|---|
| **Random Forest / tree ensemble เพียงพอ ไม่ต้อง deep learning** | **5** — 01, 02, 06, 08, 10(เทียบ) |
| **สถิติง่ายๆ จากสัญญาณพอสำหรับจำแนก** | **5** — 01, 02, 06, 09, 11 |
| **`skewness` เป็น feature มาตรฐาน** | **3** — 01, 02, 06 |
| **`entropy` เป็น feature มาตรฐาน** | **3** — 02, 06, 11 |
| **หน้าต่างยาวกว่าดีกว่า** | 1 (วัดชัด) — 10 |

---

# ส่วนที่ 4 — คำถามใน README.md ตอนนี้เป็นอย่างไร

| # | คำถาม | สถานะ | ใครตอบ |
|---|---|---|---|
| 1 | **order tracking เป็นมาตรฐานจริงไหม** | ✅ **ตอบแล้ว** | **08** (น.1) |
| 2 | **การแบ่ง train/test มาตรฐานคืออะไร** | ✅ **ตอบแล้ว** | **05, 10, 01, 04** |
| 3 | ชุด feature มาตรฐาน ขาดอะไร | 🟡 **บางส่วน** — ขาด skew กับ entropy | 01, 02, 06, 10, 11 |
| 4 | การเลือกย่าน envelope (spectral kurtosis) | ❌ **ยังไม่มีใครตอบ** | — |
| 5 | ตรวจจับด้วยข้อมูลปกติเท่านั้น | ✅ **ตอบแล้ว** | **02** (น.11, น.13) |
| 6 | **สกัด feature บน MCU ได้จริงไหม** | ❌ **ยังไม่มีใครตอบ** | 01 อ้างแต่ไม่วัด (น.5) |
| 7 | **ลายเซ็นข้ามฝั่ง** | ✅ **ยืนยันว่ามีจริง** | **06** (น.3 Table II) |

**เหลือสองข้อที่ยังต้องหา**

- **ข้อ 4 — spectral kurtosis / kurtogram** เพื่อเลือกย่าน bandpass แทนการใช้
  2–5 kHz ตายตัว **ไม่มีฉบับใดในชุดนี้ทำ envelope analysis เลยแม้แต่ฉบับเดียว**
- **ข้อ 6 — วัดเวลาสกัด feature บนไมโครคอนโทรลเลอร์จริง**
  ฉบับ 01 อ้างคำว่า lightweight edge ตลอดฉบับแต่ยอมรับเองว่าไม่เคยวัด
  (ตารางเวลาของฉบับ 05 เป็นเวลาบนคอมพิวเตอร์ ไม่ใช่ MCU)

---

# ส่วนที่ 5 — สิ่งที่ควรทำต่อ

เรียงตามผลต่องาน

| | สิ่งที่ทำ | เพราะ | ไฟล์ที่กระทบ |
|---|---|---|---|
| 1 | **ทำ order tracking** ตัดสัญญาณเป็นรอบด้วย tachometer แล้ว resample ตามมุม | ฉบับ 08 · แก้ปัญหาความเร็วที่เราวัดได้ว่ากระทบ 4 เท่า | `src/features/` ใหม่ |
| 2 | **เพิ่ม `skew` และ `spectral entropy`** | 3 ฉบับใช้ทั้งคู่ เราไม่มี | `src/features/feature_grid.py` |
| 3 | **เอา `mic` กลับมาแบบ normalize ต่อไฟล์** | ฉบับ 06 และ 01 บอกว่าเป็นช่องที่ดีที่สุด เราตัดทิ้งเร็วเกินไป | `feature_grid.py` |
| 4 | **เขียนตารางเทียบ accuracy กับวิธีแบ่ง ลงรายงาน** | เป็นจุดแข็งที่สุดที่เรามี | `docs/coop-proposal.md` |
| 5 | **อ้างอิงฉบับ 10 สำหรับการเลือกช่อง `o_tang`/`u_tang`** | ได้ขาที่สองของหลักฐาน | `docs/coop-proposal.md` §5 |
| 6 | **เพิ่มกับดัก "SMOTE ก่อนแบ่ง"** เข้ารายการกับดัก | ฉบับ 04 และ 11 เป็นตัวอย่างจริง | `CLAUDE.md` |
| 7 | **เพิ่มทางออก `unknown`** ตามฉบับ 02 | ออกแบบของเราขาดช่องนี้ | `src/service/ingest.py` |
| 8 | หา paper เรื่อง **spectral kurtosis** และ **feature extraction บน MCU** | คำถามข้อ 4 และ 6 ยังเปิด | `paper/` |
| 9 | **หา Laala et al. 2020** (ref [9] ของฉบับ 04) และ **มาตรฐาน ISO 10816 / 20816** | เป็น lead เดียวที่ใช้ envelope จริง และต้องมีฐานอ้างอิงสำหรับตารางลายเซ็น | `paper/` |

---

# คำตอบสำหรับคำถามของอาจารย์

> *"วิธีการที่ทำมาจะรู้ได้ยังไงว่าถูกต้อง"*

หลังอ่าน 11 ฉบับ ตอบได้แล้วว่า **ข้อค้นพบหลักของเรามีงานตีพิมพ์หนุนทุกข้อ**

**คอลัมน์ 🔗 กดได้ — เปิดหน้าที่เป็นหลักฐานได้ทันทีตอนคุยกับอาจารย์**

| ข้อค้นพบของเรา | วัดเองเมื่อ | งานที่หนุน | 🔗 ที่มา |
|---|---|---|---|
| tangential ดี radial แย่ | 2026-09-22 | **ฉบับ 10** (120 รอบ) | [น.3 Table II][pdf10p3] |
| ลายเซ็นข้ามฝั่งบนแกน axial | 2026-09-22 | **ฉบับ 06** (F1 100%) | [น.3 Table II][pdf06p3] |
| คลาส normal แยกยากผิดคาด | 2026-09-20 | **ฉบับ 06** (F1 6–38%) | [น.3 Table III][pdf06p3] |
| การแบ่งข้อมูลทำให้ต่าง 27 จุด | 2026-09-25 | **ฉบับ 05** (99.11%) | [น.3][pdf05p3] · [น.4][pdf05p4] |
| Random Forest พอ | ออกแบบไว้ | **5 ฉบับ** | [02 น.10][pdf02p10] · [01 น.3][pdf01p3] |
| ส่งความเร็วรอบไปกับ feature | ออกแบบไว้ | **ฉบับ 11** | [น.2][pdf11p2] |
| ความเร็วรอบกระทบตัวชี้วัด | 2026-09-20 | **ฉบับ 08** | [น.1][pdf08p1] |
| Isolation Forest สำหรับชั้น 1 | ออกแบบไว้ | **ฉบับ 02** | [น.11][pdf02p11] · [น.13][pdf02p13] |

> *"เหมือนเรากำลังงมหาด้วยตัวเอง ซึ่งมันอาจจะถูกแหละแต่มันช้า"*

อาจารย์ถูกเรื่องความเร็ว — **order tracking มีมานานแล้วและเราเพิ่งรู้**

แต่การงมหาเองก็ให้ของที่การอ่านอย่างเดียวให้ไม่ได้ **สามเรื่องนี้เรารู้แต่
วรรณกรรมชุดนี้ไม่รู้**

1. **อัตราการสุ่มจริงคือ 51,200 Hz** — 8 จาก 11 ฉบับใช้ค่าผิด และฉบับ 07
   เขียนค่าที่ขัดกันไว้ในหน้าเดียวกันโดยไม่สังเกต
2. **มวลถ่วง 0/6/20/35 g ปนอยู่ในคลาส bearing** — 10 จาก 11 ฉบับไม่เอ่ยถึงเลย
   มีเพียงฉบับ 09 ที่แสดงว่ารู้ แต่ก็ไม่ได้ใช้ควบคุมการทดลอง
3. **`o_radial` อ่อนกว่าช่องอื่น 20 เท่า** — ใช้อธิบายได้ว่าทำไมฉบับ 10 กับ 06
   จึงให้ลำดับช่องเซ็นเซอร์ที่ขัดกัน

**ของที่งมเองไม่ได้สูญเปล่า มันทำให้อ่านงานคนอื่นได้อย่างมีวิจารณญาณ**
ถ้าไม่เคยวัดด้วยตัวเอง เราจะอ่านเลข 99.11% ของฉบับ 05 แล้วเชื่อ
จะไม่เห็นว่าฉบับ 07 เขียนค่าสองค่าที่ขัดกันไว้ในหน้าเดียวกัน
และจะไม่เห็นว่าการที่ SMOTE เพิ่ม accuracy 15 จุดในฉบับ 04 และ 11
เป็นตัวเลขขนาดเดียวกับที่เราวัดได้จากการรั่วของการแบ่งข้อมูล

---

## 📂 ที่อยู่ของไฟล์เอกสาร

นิยามของปุ่มทั้งหมดในเอกสารนี้ ชี้ไปที่ไฟล์ PDF ในโฟลเดอร์ `paper/` เดียวกัน
**ถ้าเปลี่ยนชื่อไฟล์ ให้แก้ที่นี่ที่เดียว ปุ่มทุกปุ่มในเอกสารจะตามไปเอง**

<!-- ลิงก์แบบ reference-style ส่วนที่เป็น #page=N คือเลขหน้าที่จะกระโดดไป -->

[pdf01]: A%20Lightweight%20Edge%20Fusion%20Method%20for%20Multimodal%20Industrial%20IoT%20Sensor%20Data%20Feature-Level%20Processing%20and%20Fault%20Classification.pdf
[pdf01p2]: A%20Lightweight%20Edge%20Fusion%20Method%20for%20Multimodal%20Industrial%20IoT%20Sensor%20Data%20Feature-Level%20Processing%20and%20Fault%20Classification.pdf#page=2
[pdf01p3]: A%20Lightweight%20Edge%20Fusion%20Method%20for%20Multimodal%20Industrial%20IoT%20Sensor%20Data%20Feature-Level%20Processing%20and%20Fault%20Classification.pdf#page=3
[pdf01p5]: A%20Lightweight%20Edge%20Fusion%20Method%20for%20Multimodal%20Industrial%20IoT%20Sensor%20Data%20Feature-Level%20Processing%20and%20Fault%20Classification.pdf#page=5

[pdf02]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf
[pdf02p1]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=1
[pdf02p3]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=3
[pdf02p4]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=4
[pdf02p5]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=5
[pdf02p6]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=6
[pdf02p7]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=7
[pdf02p10]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=10
[pdf02p11]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=11
[pdf02p12]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=12
[pdf02p13]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=13
[pdf02p14]: A_Two-Stage_Hybrid_Architecture_for_Unknown_Anomaly_Detection_in_Rotating_Machinery_Bearings.pdf#page=14

[pdf03]: Analysis%20of%20Almost-periods%20of%20Vibration%20Signals%20of%20an%20Electric%20Motor.pdf
[pdf03p1]: Analysis%20of%20Almost-periods%20of%20Vibration%20Signals%20of%20an%20Electric%20Motor.pdf#page=1
[pdf03p2]: Analysis%20of%20Almost-periods%20of%20Vibration%20Signals%20of%20an%20Electric%20Motor.pdf#page=2
[pdf03p5]: Analysis%20of%20Almost-periods%20of%20Vibration%20Signals%20of%20an%20Electric%20Motor.pdf#page=5

[pdf04]: Classification%20of%20Mechanical%20Faults%20in%20Rotating%20Machines%20Using%20SMOTE%20Method%20and%20Deep%20Neural%20Networks.pdf
[pdf04p3]: Classification%20of%20Mechanical%20Faults%20in%20Rotating%20Machines%20Using%20SMOTE%20Method%20and%20Deep%20Neural%20Networks.pdf#page=3
[pdf04p5]: Classification%20of%20Mechanical%20Faults%20in%20Rotating%20Machines%20Using%20SMOTE%20Method%20and%20Deep%20Neural%20Networks.pdf#page=5

[pdf05]: Comparison%20of%20Machine%20Learning%20Models%20for%20Fault%20Classification%20in%20Rotating%20Machines.pdf
[pdf05p3]: Comparison%20of%20Machine%20Learning%20Models%20for%20Fault%20Classification%20in%20Rotating%20Machines.pdf#page=3
[pdf05p4]: Comparison%20of%20Machine%20Learning%20Models%20for%20Fault%20Classification%20in%20Rotating%20Machines.pdf#page=4

[pdf06]: Cutting-Edge%20Anomaly%20Detection%20for%20Predictive%20Maintenance%20Integrating%20IoT%20and%20Machine%20Learning.pdf
[pdf06p2]: Cutting-Edge%20Anomaly%20Detection%20for%20Predictive%20Maintenance%20Integrating%20IoT%20and%20Machine%20Learning.pdf#page=2
[pdf06p3]: Cutting-Edge%20Anomaly%20Detection%20for%20Predictive%20Maintenance%20Integrating%20IoT%20and%20Machine%20Learning.pdf#page=3

[pdf07]: Denoising%20Induction%20Motor%20Sounds%20Using%20an%20Autoencoder.pdf
[pdf07p1]: Denoising%20Induction%20Motor%20Sounds%20Using%20an%20Autoencoder.pdf#page=1
[pdf07p2]: Denoising%20Induction%20Motor%20Sounds%20Using%20an%20Autoencoder.pdf#page=2

[pdf08]: Fault%20Classification%20in%20Rotating%20Machinery%20using%20Inverse%20Physics-Informed%20Neural%20Networks.pdf
[pdf08p1]: Fault%20Classification%20in%20Rotating%20Machinery%20using%20Inverse%20Physics-Informed%20Neural%20Networks.pdf#page=1

[pdf09]: Fault%20Diagnosis%20of%20Electrical%20Motors%20from%20Multivariate%20Time-Series%20Data%20Using%20Hybrid%20Models.pdf
[pdf09p2]: Fault%20Diagnosis%20of%20Electrical%20Motors%20from%20Multivariate%20Time-Series%20Data%20Using%20Hybrid%20Models.pdf#page=2
[pdf09p3]: Fault%20Diagnosis%20of%20Electrical%20Motors%20from%20Multivariate%20Time-Series%20Data%20Using%20Hybrid%20Models.pdf#page=3
[pdf09p5]: Fault%20Diagnosis%20of%20Electrical%20Motors%20from%20Multivariate%20Time-Series%20Data%20Using%20Hybrid%20Models.pdf#page=5

[pdf10]: Quantifying%20Factor%20Effects%20in%20Signal-to-Image%20Fault%20Detect%20and%20Diagnosis.pdf
[pdf10p2]: Quantifying%20Factor%20Effects%20in%20Signal-to-Image%20Fault%20Detect%20and%20Diagnosis.pdf#page=2
[pdf10p3]: Quantifying%20Factor%20Effects%20in%20Signal-to-Image%20Fault%20Detect%20and%20Diagnosis.pdf#page=3

[pdf11]: The%20Influence%20of%20Handling%20Imbalance%20Classes%20on%20the%20Classification%20of%20Mechanical%20Faults%20Using%20Neural%20Networks.pdf
[pdf11p1]: The%20Influence%20of%20Handling%20Imbalance%20Classes%20on%20the%20Classification%20of%20Mechanical%20Faults%20Using%20Neural%20Networks.pdf#page=1
[pdf11p2]: The%20Influence%20of%20Handling%20Imbalance%20Classes%20on%20the%20Classification%20of%20Mechanical%20Faults%20Using%20Neural%20Networks.pdf#page=2
[pdf11p3]: The%20Influence%20of%20Handling%20Imbalance%20Classes%20on%20the%20Classification%20of%20Mechanical%20Faults%20Using%20Neural%20Networks.pdf#page=3
[pdf11p4]: The%20Influence%20of%20Handling%20Imbalance%20Classes%20on%20the%20Classification%20of%20Mechanical%20Faults%20Using%20Neural%20Networks.pdf#page=4

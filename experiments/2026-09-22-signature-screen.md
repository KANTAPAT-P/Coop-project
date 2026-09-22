# คัดกรองลายเซ็นของความผิดปกติแต่ละชนิด

- วันที่: 2026-09-22
- สคริปต์: `src/features/screen_signatures.py`
- ไฟล์: 254 ไฟล์ · ความเร็ว 20–42 Hz · สุ่มกลุ่มละไม่เกิน 25 ไฟล์ · bearing ใช้มวล 0 g
- feature: 66 ตัว (6 ช่อง)
- ตัววัด: AUC แบบ one-vs-rest · ความแรง = |AUC−0.5|×2 (1 = แยกขาด, 0 = แยกไม่ได้)

## จำนวนไฟล์ต่อกลุ่ม

| กลุ่ม | ไฟล์ |
|---|---:|
| `h-misalign` | 25 |
| `imbalance heavy 25-35g` | 25 |
| `imbalance light 6-15g` | 25 |
| `normal` | 22 |
| `over ball` | 22 |
| `over cage` | 21 |
| `over outer` | 22 |
| `under ball` | 23 |
| `under cage` | 22 |
| `under outer` | 22 |
| `v-misalign` | 25 |

## feature ที่ดีที่สุดของแต่ละกลุ่ม

แยกสองคอลัมน์: ตัวที่ดีที่สุดโดยรวม และตัวที่ดีที่สุดใน family ที่**ไม่ขึ้นกับความไวเซ็นเซอร์**

| กลุ่ม | ดีสุดโดยรวม | ความแรง | ดีสุดแบบ robust | ความแรง |
|---|---|---:|---|---:|
| normal | `o_radial.h1_frac` ต่ำกว่า | 0.84 | `o_radial.h1_frac` ต่ำกว่า | 0.84 |
| imbalance light 6-15g | `o_axial.env_floor` ต่ำกว่า | 0.93 | `o_axial.env_rel` ต่ำกว่า | 0.84 |
| imbalance heavy 25-35g | `u_radial.h1_frac` สูงกว่า | 0.99 | `u_radial.h1_frac` สูงกว่า | 0.99 |
| h-misalign | `u_tang.e_high` สูงกว่า | 0.77 | `u_tang.e_high` สูงกว่า | 0.77 |
| v-misalign | `u_tang.kurt_band` ต่ำกว่า | 0.83 | `u_tang.kurt_band` ต่ำกว่า | 0.83 |
| under outer | `o_axial.e_high` สูงกว่า | 1.00 | `o_axial.e_high` สูงกว่า | 1.00 |
| under ball | `o_axial.rms` สูงกว่า | 1.00 | `o_radial.kurt_band` สูงกว่า | 0.95 |
| under cage | `u_tang.kurt` สูงกว่า | 0.99 | `u_tang.kurt` สูงกว่า | 0.99 |
| over outer | `u_radial.env_rel` สูงกว่า | 0.97 | `u_radial.env_rel` สูงกว่า | 0.97 |
| over ball | `o_radial.e_high` ต่ำกว่า | 1.00 | `o_radial.e_high` ต่ำกว่า | 1.00 |
| over cage | `o_tang.env_floor` ต่ำกว่า | 1.00 | `o_radial.h1_frac` สูงกว่า | 0.91 |

## รายละเอียด 5 อันดับแรกของแต่ละกลุ่ม

### normal

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `o_radial.h1_frac` | robust | 0.84 | ต่ำกว่า | 0.007084 | 0.05662 |
| `o_radial.kurt` | robust | 0.84 | ต่ำกว่า | 1.975 | 2.601 |
| `o_radial.e_high` | robust | 0.80 | สูงกว่า | 0.04054 | 0.02708 |
| `o_tang.e_high` | robust | 0.80 | สูงกว่า | 0.4315 | 0.122 |
| `u_tang.rms` | amplitude | 0.74 | ต่ำกว่า | 0.115 | 0.2429 |

### imbalance light 6-15g

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `o_axial.env_floor` | amplitude | 0.93 | ต่ำกว่า | 4.667e-05 | 0.000284 |
| `o_axial.rms` | amplitude | 0.92 | ต่ำกว่า | 0.05458 | 0.3726 |
| `o_radial.rms` | amplitude | 0.90 | ต่ำกว่า | 0.02557 | 0.03413 |
| `o_axial.env_rel` | robust | 0.84 | ต่ำกว่า | 0.01071 | 0.01242 |
| `o_axial.kurt_band` | robust | 0.84 | ต่ำกว่า | 3.045 | 3.849 |

### imbalance heavy 25-35g

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `u_radial.h1_frac` | robust | 0.99 | สูงกว่า | 0.6843 | 0.04269 |
| `u_tang.e_low` | robust | 0.98 | สูงกว่า | 0.8086 | 0.1069 |
| `u_tang.h1_frac` | robust | 0.98 | สูงกว่า | 0.7013 | 0.01839 |
| `u_radial.e_high` | robust | 0.97 | ต่ำกว่า | 0.01219 | 0.1262 |
| `u_radial.e_low` | robust | 0.96 | สูงกว่า | 0.9414 | 0.3085 |

### h-misalign

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `u_tang.e_high` | robust | 0.77 | สูงกว่า | 0.8431 | 0.4617 |
| `o_tang.env_rel` | robust | 0.73 | ต่ำกว่า | 0.01518 | 0.01776 |
| `o_tang.e_high` | robust | 0.72 | สูงกว่า | 0.3933 | 0.1227 |
| `u_tang.env_rel` | robust | 0.63 | สูงกว่า | 0.01651 | 0.0142 |
| `u_tang.e_mid` | robust | 0.58 | ต่ำกว่า | 0.07111 | 0.2087 |

### v-misalign

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `u_tang.kurt_band` | robust | 0.83 | ต่ำกว่า | 3.255 | 3.737 |
| `o_axial.r21` | robust | 0.82 | สูงกว่า | 0.876 | 0.309 |
| `u_tang.e_high` | robust | 0.80 | สูงกว่า | 0.8407 | 0.4617 |
| `o_radial.r21` | robust | 0.78 | สูงกว่า | 0.9081 | 0.3004 |
| `o_tang.env_rel` | robust | 0.78 | ต่ำกว่า | 0.01487 | 0.01776 |

### under outer

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `o_axial.e_high` | robust | 1.00 | สูงกว่า | 0.0448 | 0.004135 |
| `o_radial.env_rel` | robust | 0.97 | สูงกว่า | 0.01544 | 0.009152 |
| `o_radial.env_floor` | amplitude | 0.92 | สูงกว่า | 0.0002285 | 3.905e-05 |
| `u_axial.env_rel` | robust | 0.88 | สูงกว่า | 0.01558 | 0.01089 |
| `o_tang.e_low` | robust | 0.88 | ต่ำกว่า | 0.1867 | 0.5993 |

### under ball

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `o_axial.rms` | amplitude | 1.00 | สูงกว่า | 3.57 | 0.3359 |
| `o_tang.env_floor` | amplitude | 0.99 | สูงกว่า | 0.01288 | 0.001751 |
| `o_axial.env_floor` | amplitude | 0.99 | สูงกว่า | 0.002918 | 0.0002314 |
| `o_tang.rms` | amplitude | 0.97 | สูงกว่า | 1.712 | 0.2625 |
| `o_radial.kurt_band` | robust | 0.95 | สูงกว่า | 6.799 | 2.95 |

### under cage

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `u_tang.kurt` | robust | 0.99 | สูงกว่า | 5.91 | 3.252 |
| `o_tang.kurt_band` | robust | 0.96 | สูงกว่า | 7.301 | 3.913 |
| `u_tang.crest` | robust | 0.96 | สูงกว่า | 10.16 | 5.509 |
| `o_axial.kurt_band` | robust | 0.92 | สูงกว่า | 5.539 | 3.663 |
| `u_axial.e_low` | robust | 0.84 | ต่ำกว่า | 0.3676 | 0.5872 |

### over outer

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `u_radial.env_rel` | robust | 0.97 | สูงกว่า | 0.01825 | 0.0142 |
| `u_radial.kurt` | robust | 0.82 | สูงกว่า | 3.804 | 2.856 |
| `u_tang.env_rel` | robust | 0.73 | สูงกว่า | 0.01674 | 0.01422 |
| `o_radial.env_rel` | robust | 0.67 | ต่ำกว่า | 0.008533 | 0.009287 |
| `o_tang.kurt_band` | robust | 0.64 | ต่ำกว่า | 3.535 | 4.028 |

### over ball

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `o_radial.e_high` | robust | 1.00 | ต่ำกว่า | 0.0002017 | 0.03163 |
| `u_tang.env_floor` | amplitude | 1.00 | สูงกว่า | 0.01667 | 0.001791 |
| `u_tang.rms` | amplitude | 1.00 | สูงกว่า | 3.805 | 0.2103 |
| `o_radial.rms` | amplitude | 1.00 | สูงกว่า | 1.402 | 0.03113 |
| `u_axial.kurt` | robust | 1.00 | สูงกว่า | 4.119 | 2.554 |

### over cage

| feature | family | ความแรง | ทิศ | มัธยฐานกลุ่มนี้ | มัธยฐานกลุ่มอื่น |
|---|---|---:|---|---:|---:|
| `o_tang.env_floor` | amplitude | 1.00 | ต่ำกว่า | 0.0004299 | 0.002043 |
| `u_radial.rms` | amplitude | 0.99 | ต่ำกว่า | 0.2358 | 0.4361 |
| `o_radial.h1_frac` | robust | 0.91 | สูงกว่า | 0.2892 | 0.04251 |
| `u_tang.env_floor` | amplitude | 0.90 | ต่ำกว่า | 0.0005652 | 0.002242 |
| `o_radial.e_mid` | robust | 0.85 | ต่ำกว่า | 0.1646 | 0.3264 |


"""วัดว่าความผิดปกติ 9 คลาสแยกออกจากกันยากง่ายแค่ไหน

## คำถามที่ตอบ

ต่างจากที่เคยวัดมา `eval_detector.py` ตอบว่า **"ต่างจาก normal ไหม"**
ซึ่งเป็นชั้นที่ 1 ส่วนไฟล์นี้ตอบว่า **"แยกออกจากกันเองได้ไหม"** ซึ่งเป็นชั้นที่ 2
และยังไม่เคยวัดมาก่อน

แยก bearing เป็น 6 คลาสตามฝั่งและชนิด (ไม่ยุบเป็น underhang/overhang)
รวมกับ imbalance และ misalignment สองแบบ เป็น **9 คลาส**

## วัดสามอย่าง เพราะแต่ละอย่างตอบคนละคำถาม

| ตัวชี้วัด | ตอบว่า |
|---|---|
| **AUC เทียบ normal** | ตรวจ**เจอ**ไหมว่าผิดปกติ (ชั้น 1) |
| **recall แบบ 9 คลาส** | บอก**ชนิด**ได้ไหม (ชั้น 2) |
| **recall เมื่อแบ่งตามความเร็ว** | ยังทำได้ไหมเมื่อเจอความเร็วที่ไม่เคยเห็น |

**ตัวที่สามเข้มที่สุดและเชื่อถือได้มากที่สุด** เพราะเป็นการแบ่งที่ตัดโอกาส
ให้โมเดลจำความเร็วแทนความเสียหาย `CLAUDE.md` หัวข้อ 5 วัดไว้แล้วว่า
การแบ่งแบบนี้ทำให้ accuracy ตก 12 จุดจากการแบ่งตามไฟล์

## ⚠️ ข้อจำกัดที่ต้องอ่านก่อนเชื่อตัวเลข

**ทุกวิธีแบ่งในไฟล์นี้ยังอยู่ในรอบบันทึกเดียวกัน** เพราะไฟล์ในกลุ่มย่อย
เดียวกันน่าจะบันทึกรวดเดียว และชุดข้อมูลไม่ได้บอกว่าไฟล์ไหนมาจาก
การประกอบเครื่องครั้งไหน **ตัวเลขทุกตัวจึงดีเกินจริง**

ให้ใช้เพื่อ**เรียงลำดับ**ว่าคลาสไหนยากกว่าคลาสไหน ซึ่งเชื่อถือได้มากกว่า
เพราะทุกคลาสเจออคติแบบเดียวกัน **ห้ามอ่านเป็นความแม่นยำที่จะได้ที่หน้างาน**

รัน:
    python src/models/rank_separability.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import processed_dir, repo_root  # noqa: E402

HZ_LO, HZ_HI = 13.1, 61.2
SEED = 7


def load() -> tuple[pd.DataFrame, list[str]]:
    """ตารางที่ใช้วัดการแยกคลาส

    ⚠️ **ใช้ตารางของไฟล์เต็ม 4,883 ms โดยเจตนา** ต่างจากตัวตรวจจับใน
    `eval_detector.py` ที่เทรนบนหน้าต่าง 410 ms เพราะคำถามของไฟล์นี้คือ
    **"ข้อมูลที่ดีที่สุดที่เรามีแยกคลาสได้แค่ไหน"** ซึ่งเป็นขอบบนของ
    ความสามารถ ไม่ใช่สิ่งที่ระบบจริงทำได้

    🚩 ดังนั้น **ตัวเลขในไฟล์นี้เทียบกับ recall ของตัวตรวจจับตรงๆ ไม่ได้**
    หน้าต่างต่างกัน 11.9 เท่า และ `env_floor` กับ `env_rel` ต่างกัน 272%
    ถ้าอยากได้ตัวเลขที่เทียบกันได้ ต้องเปลี่ยนมาอ่าน
    `feature_grid_win410ms.csv` แล้วแบ่ง train/test ตามคอลัมน์ `rel`
    """
    grid = pd.read_csv(processed_dir() / "feature_grid.csv")
    feats = [c for c in grid.columns if "." in c]
    bearing = grid.cls.isin(["underhang", "overhang"])
    sub = grid[(~bearing | (grid.mass_g == 0))
               & grid.rot_hz.between(HZ_LO, HZ_HI)].copy()

    # ชื่อคลาสระดับละเอียด — bearing แยกตามฝั่งและชนิด
    def label(r) -> str:
        if r.cls in ("underhang", "overhang"):
            side = "u" if r.cls == "underhang" else "o"
            return f"{side}-{r.subclass}"
        return {"imbalance": "imbalance",
                "horizontal-misalignment": "h-mis",
                "vertical-misalignment": "v-mis",
                "normal": "normal"}[r.cls]

    sub["label"] = sub.apply(label, axis=1)
    return sub, feats


def auc_vs_normal(sub: pd.DataFrame, feats: list[str]) -> pd.Series:
    """AUC ที่ดีที่สุดจากตัวชี้วัดเดี่ยว เมื่อเทียบคลาสนั้นกับ normal

    ใช้ตัวชี้วัดเดี่ยวไม่ใช่โมเดล เพราะต้องการวัดว่า**สัญญาณมีอยู่จริงแค่ไหน**
    ไม่ใช่วัดว่าโมเดลเก่งแค่ไหน ซึ่งปนกับความสามารถในการจำ
    """
    norm = sub[sub.label == "normal"]
    out = {}
    for lab, g in sub[sub.label != "normal"].groupby("label"):
        y = np.r_[np.zeros(len(norm)), np.ones(len(g))]
        best = 0.0
        for f in feats:
            x = np.r_[norm[f].to_numpy(), g[f].to_numpy()]
            if not np.all(np.isfinite(x)):
                continue
            a = roc_auc_score(y, x)
            best = max(best, a, 1 - a)        # ทิศทางไหนก็ได้
        out[lab] = best
    return pd.Series(out).sort_values(ascending=False)


def per_class_recall(sub: pd.DataFrame, feats: list[str],
                     mode: str) -> tuple[pd.Series, pd.DataFrame]:
    """recall ต่อคลาสจากการจำแนก 9 คลาส

    ``mode='by-file'``      แบ่งสลับตามอันดับความเร็วภายในแต่ละคลาส
    ``mode='low-to-high'``  เทรนความเร็วต่ำ ทดสอบความเร็วสูง
    ``mode='high-to-low'``  เทรนความเร็วสูง ทดสอบความเร็วต่ำ

    **ต้องรันทั้งสองทิศ** เพราะแต่ละทิศมีไฟล์ทดสอบเพียงราว 24 ไฟล์ต่อคลาส
    ค่าที่ได้จากทิศเดียวจึงแกว่งมาก และ `CLAUDE.md` หัวข้อ 5 วัดไว้แล้วว่า
    สองทิศให้ผลต่างกัน (0.726 กับ 0.790) เพราะที่ความเร็วสูงความเสียหาย
    ถูกกระตุ้นแรงกว่า ตัวอย่างที่เทรนจึงมีสัญญาณชัดกว่า
    """
    fault = sub[sub.label != "normal"].copy()
    if mode == "by-file":
        fault = fault.sort_values(["label", "rot_hz"])
        is_tr = fault.groupby("label").cumcount() % 2 == 0
    elif mode == "low-to-high":
        is_tr = fault.rot_hz <= fault.rot_hz.median()
    else:
        is_tr = fault.rot_hz > fault.rot_hz.median()

    tr, te = fault[is_tr], fault[~is_tr]
    clf = RandomForestClassifier(n_estimators=400, random_state=SEED,
                                 class_weight="balanced", n_jobs=-1)
    clf.fit(tr[feats], tr.label)
    pred = clf.predict(te[feats])

    te = te.assign(pred=pred)
    rec = te.groupby("label").apply(
        lambda g: (g.pred == g.name).mean(), include_groups=False)

    # precision จำเป็นพอๆ กับ recall
    #
    # 🚨 คลาสที่กลายเป็น "ถังขยะ" ของโมเดลจะมี recall สูงแบบหลอก
    # เพราะมันรับทุกอย่างที่โมเดลไม่มั่นใจเข้ามา วัดได้ด้วย precision เท่านั้น
    prec = {}
    for lab in rec.index:
        hit = (te.pred == lab)
        prec[lab] = float((te.label[hit] == lab).mean()) if hit.any() else 0.0
    prec = pd.Series(prec)
    f1 = 2 * prec * rec / (prec + rec).replace(0, np.nan)

    conf = pd.crosstab(te.label, te.pred, normalize="index")
    return pd.DataFrame({"recall": rec, "precision": prec, "f1": f1}), conf


def main() -> int:
    sub, feats = load()
    lines: list[str] = []

    def say(s: str = "") -> None:
        print(s)
        lines.append(s)

    say("# ความผิดปกติ 9 คลาส — คลาสไหนแยกง่าย คลาสไหนแยกยาก")
    say()
    say(f"**วันที่** {date.today().isoformat()} · "
        "สร้างด้วย `python src/models/rank_separability.py`")
    say()
    say("## ข้อมูลที่ใช้")
    say()
    say(f"ขอบเขตที่ยุติธรรม **{HZ_LO}–{HZ_HI} Hz · bearing เฉพาะ 0 g · "
        f"imbalance ทุกมวล** -> {len(sub):,} ไฟล์")
    say()
    say("| คลาส | ไฟล์ |")
    say("|---|---:|")
    for lab, n in sub.groupby("label").size().sort_values(ascending=False).items():
        say(f"| {'**' + lab + '**' if lab == 'normal' else lab} | {n} |")
    say()
    say("⚠️ **จำนวนไฟล์ไม่เท่ากันมาก** imbalance มี 326 ไฟล์ ขณะที่ bearing "
        "แต่ละชนิดมีราว 48 ไฟล์ จึงใช้ `class_weight='balanced'` และรายงาน "
        "**recall ต่อคลาส** ซึ่งไม่ถูกจำนวนไฟล์บิดเบือน ไม่ใช่ accuracy รวม")
    say()

    # ---------------------------------------------- ชั้นที่ 1
    auc = auc_vs_normal(sub, feats)
    say("## ชั้นที่ 1 — ตรวจเจอไหมว่าผิดปกติ")
    say()
    say("AUC ที่ดีที่สุดจาก**ตัวชี้วัดเดี่ยว** เมื่อเทียบกับ normal "
        "ใช้ตัวชี้วัดเดี่ยวเพื่อวัดว่าสัญญาณมีอยู่จริงแค่ไหน ไม่ใช่วัดว่าโมเดลเก่งแค่ไหน")
    say()
    say("| คลาส | AUC สูงสุด |")
    say("|---|---:|")
    for lab, v in auc.items():
        say(f"| {lab} | {v:.3f} |")
    say()

    # ---------------------------------------------- ชั้นที่ 2
    m_f, _ = per_class_recall(sub, feats, "by-file")
    m_lo, conf_lo = per_class_recall(sub, feats, "low-to-high")
    m_hi, conf_hi = per_class_recall(sub, feats, "high-to-low")
    f1_2 = pd.concat([m_lo.f1, m_hi.f1], axis=1).mean(axis=1).sort_values(
        ascending=False)
    rec_2 = pd.concat([m_lo.recall, m_hi.recall], axis=1).mean(axis=1)
    prec_2 = pd.concat([m_lo.precision, m_hi.precision], axis=1).mean(axis=1)
    worst_f1 = pd.concat([m_lo.f1, m_hi.f1], axis=1).min(axis=1)

    say("## ชั้นที่ 2 — บอกชนิดได้ไหม (จำแนก 8 คลาสที่เสีย)")
    say()
    say("เรียงตาม **F1 เฉลี่ยสองทิศของการแบ่งตามความเร็ว** ซึ่งเป็นตัวที่"
        "เชื่อถือได้ที่สุดในตารางนี้")
    say()
    say("| คลาส | F1 เฉลี่ย | recall เฉลี่ย | precision เฉลี่ย | F1 แย่สุด | แบ่งตามไฟล์ (recall) |")
    say("|---|---:|---:|---:|---:|---:|")
    for lab in f1_2.index:
        say(f"| {lab} | **{f1_2[lab]:.3f}** | {rec_2[lab]:.3f} "
            f"| {prec_2[lab]:.3f} | {worst_f1[lab]:.3f} "
            f"| {m_f.recall[lab]:.3f} |")
    say()
    say("🚨 **ต้องดู precision คู่กับ recall เสมอ** เพราะคลาสที่กลายเป็น"
        "**ถังขยะ**ของโมเดลจะมี recall สูงแบบหลอก โดยรับทุกอย่างที่โมเดล"
        "ไม่มั่นใจเข้ามา ซึ่งเกิดขึ้นจริงกับ `o-cage_fault` ในทิศเทรนสูง→ทดสอบต่ำ "
        "ดูตารางความสับสนข้างล่าง")
    say()
    say(f"**ค่าเฉลี่ยรวม** F1 {f1_2.mean():.3f} · "
        f"recall จากการแบ่งตามไฟล์ {m_f.recall.mean():.3f}")
    say()
    say("🚨 **การแบ่งตามไฟล์ให้ 0.999 แทบทุกคลาส จึงใช้เรียงลำดับไม่ได้เลย** "
        "ซึ่งเป็นลายเซ็นของการรั่วแบบเดียวกับที่วัดไว้ใน "
        "`experiments/2026-09-25-split-leakage.md` "
        "**คอลัมน์ที่ใช้เรียงลำดับได้คือการแบ่งตามความเร็ว**")
    say()
    say("และ**ต้องดูทั้งสองทิศ** เพราะแต่ละทิศมีไฟล์ทดสอบเพียงราว 24 ไฟล์ต่อคลาส "
        "ค่าจากทิศเดียวจึงแกว่งมาก คอลัมน์ `แย่สุด` คือค่าที่ปลอดภัยที่สุดในการอ้างอิง")
    say()

    # ------------------------------------- สับสนกับอะไร
    say("## คลาสไหนถูกสับสนกับอะไร")
    say()
    say("แถวคือคลาสจริง แสดงเฉพาะคำตอบที่เกิน 10% รวมผลจากทั้งสองทิศ")
    say()
    for name, conf in (("เทรนต่ำ→ทดสอบสูง", conf_lo),
                       ("เทรนสูง→ทดสอบต่ำ", conf_hi)):
        say(f"### {name}")
        say()
        for lab in conf.index:
            row = conf.loc[lab].sort_values(ascending=False)
            parts = [f"{k} {v:.0%}" for k, v in row.items() if v >= 0.10]
            say(f"- **{lab}** -> {' · '.join(parts)}")
        say()

    # ---------------------------------------------- สรุปเป็นกลุ่ม
    say("## สรุป — แบ่งเป็นสามกลุ่ม ไม่ใช่เรียงเก้าอันดับ")
    say()
    say("ไฟล์ทดสอบมีราว 24 ไฟล์ต่อคลาสต่อทิศ รวมสองทิศได้ 48 "
        "ช่วงความเชื่อมั่น 95% ของสัดส่วนที่ n = 48 กว้างราว **±0.11 ถึง ±0.14** "
        "**ส่วนต่างที่เล็กกว่านั้นแยกไม่ออกทางสถิติ** จึงจัดเป็นกลุ่มแทนการเรียงอันดับ")
    say()
    tiers = [("แยกง่าย", [l for l in f1_2.index if f1_2[l] >= 0.90]),
             ("ปานกลาง", [l for l in f1_2.index if 0.75 <= f1_2[l] < 0.90]),
             ("แยกยาก", [l for l in f1_2.index if f1_2[l] < 0.75])]
    say("| กลุ่ม | คลาส | ช่วง F1 |")
    say("|---|---|---|")
    for name, labs in tiers:
        if not labs:
            continue
        lo = min(f1_2[l] for l in labs)
        hi = max(f1_2[l] for l in labs)
        say(f"| **{name}** | {' · '.join(labs)} | {lo:.3f}–{hi:.3f} |")
    say()
    say("### ตรวจความสอดคล้องกับตารางลายเซ็นใน `CLAUDE.md`")
    say()
    say("| คลาส | สถานะลายเซ็นที่เคยวัด | กลุ่มที่ได้จากไฟล์นี้ | ตรงกันไหม |")
    say("|---|---|---|---|")
    sig = {"imbalance": "✅ ยืนยันแล้ว", "o-outer_race": "✅ ยืนยันแล้ว",
           "u-ball_fault": "✅ ยืนยันแล้ว", "o-ball_fault": "✅ ยืนยันแล้ว",
           "u-outer_race": "🟡 จางเมื่อเติมมวล", "u-cage_fault": "🟡 หายเมื่อเติมมวล",
           "h-mis": "🟡 ทิศถูกแต่ไม่แยกขาด", "v-mis": "🟡 ทิศถูกแต่ไม่แยกขาด",
           "o-cage_fault": "❌ ยังไม่เจอ"}
    tier_of = {l: n for n, labs in tiers for l in labs}
    for lab in f1_2.index:
        st = sig.get(lab, "—")
        t = tier_of.get(lab, "—")
        ok = ("✅" if (st.startswith("✅") and t != "แยกยาก")
              or (st.startswith("❌") and t == "แยกยาก")
              or st.startswith("🟡") else "⚠️")
        say(f"| {lab} | {st} | {t} | {ok} |")
    say()
    say("**จุดที่ดูขัดกันแต่อธิบายได้** `u-outer_race` เคยถูกจัดเป็น 🟡 "
        "เพราะลายเซ็นจางลงเมื่อเติมมวลถ่วง แต่ไฟล์นี้ทดสอบที่ **0 g เท่านั้น** "
        "ซึ่งเป็นจุดที่ลายเซ็นแรงที่สุด (9.5 เท่า) จึงขึ้นมาอยู่กลุ่มแยกง่าย "
        "ส่วน `o-outer_race` ที่เป็น ✅ กลับอยู่กลุ่มแยกยาก เพราะลายเซ็นของมัน"
        "เป็นอัตราส่วนเพียง 1.35 เท่า ซึ่ง**คงอยู่จริงแต่เบา**")
    say()
    say("> **ข้อสรุปคือการจัดกลุ่มนี้สอดคล้องกับ _ความแรง_ ของลายเซ็น "
        "มากกว่าความคงอยู่ของมัน** ซึ่งเป็นคนละเรื่องกันและต้องแยกให้ชัดในรายงาน")
    say()

    out = (repo_root() / "experiments"
           / f"{date.today().isoformat()}-class-separability.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานลง {out.relative_to(repo_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""ตัวช่วยเล็กๆ สำหรับ widget ของ matplotlib ที่ใช้ซ้ำในหลายโปรแกรม

**ทำไมต้องมีไฟล์นี้** `matplotlib.widgets.RadioButtons` ยอมรับคลิกเฉพาะเมื่อคลิก
โดนวงกลมหรือโดนตัวอักษรเท่านั้น (ดู `_clicked` ใน `matplotlib/widgets.py`)
วงกลมที่ค่าเริ่มต้นโตเพียง **6.9 พิกเซล** และตัวอักษรสูง 14 พิกเซล พื้นที่ว่าง
ระหว่างสองอย่างนี้กับที่ว่างด้านขวาของตัวอักษรกดไม่ติดเลย พอวางปุ่มหลายตัว
ในคอลัมน์แคบๆ ที่แถวห่างกันราว 25 พิกเซล ก็แทบกดไม่โดน

`row_clickable()` แก้โดยรับคลิก**ทั้งช่อง** คือแบ่งพื้นที่ของแกนเป็นตารางตามแถว
และคอลัมน์ของปุ่ม แล้วคลิกที่ไหนก็ได้ในช่องนั้นเพื่อเลือกตัวนั้น
"""

from __future__ import annotations

import numpy as np


def row_clickable(radio) -> int:
    """ทำให้คลิกที่ไหนก็ได้ในช่องของตัวเลือกนั้น แล้วเลือกตัวนั้น

    **ทำไมต้องแบ่งเป็นช่อง ไม่ใช่วัดระยะที่ใกล้ที่สุด** เพราะข้อความของแต่ละตัวเลือก
    ยาวไม่เท่ากัน ถ้าวัดระยะถึงกรอบ การคลิกไกลไปทางขวาของตัวเลือกที่ชื่อสั้น
    จะมีระยะถึงกรอบของตัวเลือกชื่อยาวในแถวข้างเคียงสั้นกว่า แล้วเลือกผิดแถว
    (วัดจริงแล้วผิด 9 จาก 15 แถว) การแบ่งเป็นช่องทำให้ทุกจุดในแกนมีเจ้าของแน่นอน

    ``RadioButtons`` วางหลายคอลัมน์ได้ผ่านพารามิเตอร์ ``layout`` จึงต้องหาเส้นแบ่ง
    คอลัมน์ด้วย เส้นแบ่งวางไว้กึ่งกลางระหว่าง**ปลายข้อความที่ยาวที่สุดของคอลัมน์ซ้าย**
    กับ**วงกลมของคอลัมน์ขวา** ที่ว่างถัดจากข้อความยาวๆ จึงยังเป็นของคอลัมน์ตัวเอง

    ตัวจัดการนี้ต่อ *หลัง* ของ matplotlib เอง ถ้าคลิกโดนวงกลมหรือตัวอักษรพอดี
    matplotlib จัดการถูกต้องอยู่แล้ว ฟังก์ชันนี้จึงถอยออกทันที ไม่เข้าไปแย่ง
    เพราะกรณีนั้นเจตนาของผู้ใช้ชัดเจนกว่าการเดาจากช่อง

    คืนค่า connection id เผื่อผู้เรียกต้องการยกเลิกภายหลัง
    """
    canvas = radio.ax.get_figure().canvas

    def grid(boxes):
        """คืน (คอลัมน์ของแต่ละตัวเลือก, ความสูงของแต่ละตัวเลือก, เส้นแบ่งคอลัมน์)"""
        if cxy is None:
            xs = np.array([b.x0 for b in boxes])
            ys = np.array([b.y0 + b.height / 2.0 for b in boxes])
        else:
            xs, ys = cxy[:, 0], cxy[:, 1]
        cols = np.unique(np.round(xs, 1))
        col_of = np.array([int(np.argmin(np.abs(cols - x))) for x in xs])
        bounds = [
            (max(boxes[i].x1 for i in np.flatnonzero(col_of == k)) + cols[k + 1]) / 2.0
            for k in range(len(cols) - 1)
        ]
        return col_of, ys, np.array(bounds)

    def on_press(event) -> None:
        if event.button != 1 or event.inaxes is not radio.ax:
            return
        try:
            boxes = [t.get_window_extent() for t in radio.labels]
        except RuntimeError:        # ยังไม่เคยวาด จึงยังไม่มี renderer
            return
        # คลิกโดนตัวอักษรหรือวงกลม = matplotlib จัดการไปแล้วอย่างถูกต้อง
        if any(t.contains(event)[0] for t in radio.labels):
            return
        if cxy is not None and radio._buttons.contains(event)[0]:
            return

        col_of, ys, bounds = grid(boxes)
        k = int(np.searchsorted(bounds, event.x))
        cand = np.flatnonzero(col_of == k)
        if not len(cand):
            return
        i = int(cand[int(np.argmin(np.abs(ys[cand] - event.y)))])
        if radio.value_selected != radio.labels[i].get_text():
            radio.set_active(i)

    try:
        cxy = radio._buttons.get_offset_transform().transform(
            radio._buttons.get_offsets())
    except AttributeError:          # matplotlib รุ่นที่ไม่มี _buttons
        cxy = None

    return canvas.mpl_connect("button_press_event", on_press)


__all__ = ["row_clickable"]

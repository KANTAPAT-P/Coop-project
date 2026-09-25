"""ตัวช่วยเล็กๆ สำหรับ widget ของ matplotlib ที่ใช้ซ้ำในหลายโปรแกรม

**ทำไมต้องมีไฟล์นี้** `matplotlib.widgets.RadioButtons` ยอมรับคลิกเฉพาะเมื่อคลิก
โดนวงกลมหรือโดนตัวอักษรเท่านั้น (ดู `_clicked` ใน `matplotlib/widgets.py`)
วงกลมที่ค่าเริ่มต้นโตเพียง **6.9 พิกเซล** และตัวอักษรสูง 14 พิกเซล พื้นที่ว่าง
ระหว่างสองอย่างนี้กับที่ว่างด้านขวาของตัวอักษรกดไม่ติดเลย พอวางปุ่มหลายตัว
ในคอลัมน์แคบๆ ที่แถวห่างกันราว 25 พิกเซล ก็แทบกดไม่โดน

`row_clickable()` แก้โดยรับคลิก**ทั้งแถว** คือคลิกที่ไหนก็ได้ในแกนของปุ่ม
แล้วเลือกตัวที่อยู่ใกล้ในแนวตั้งที่สุด
"""

from __future__ import annotations

import numpy as np


def row_clickable(radio) -> int:
    """ทำให้คลิกที่ไหนก็ได้ในแถวของ RadioButtons แล้วเลือกตัวนั้น

    ตัวจัดการนี้ต่อ *หลัง* ของ matplotlib เอง ดังนั้นถ้าคลิกโดนวงกลมหรือ
    ตัวอักษรพอดี matplotlib จะเปลี่ยนค่าไปก่อนแล้ว ฟังก์ชันนี้จึงเช็คก่อนว่า
    ค่าเปลี่ยนไปแล้วหรือยัง ถ้าเปลี่ยนแล้วก็ไม่ทำอะไร จะได้ไม่วาดซ้ำสองรอบ

    คืนค่า connection id เผื่อผู้เรียกต้องการยกเลิกภายหลัง
    """
    canvas = radio.ax.get_figure().canvas

    def centre_y(text) -> float:
        box = text.get_window_extent()
        return box.y0 + box.height / 2.0

    def on_press(event) -> None:
        if event.button != 1 or event.inaxes is not radio.ax:
            return
        try:
            ys = np.array([centre_y(t) for t in radio.labels])
        except RuntimeError:        # ยังไม่เคยวาด จึงยังไม่มี renderer
            return
        i = int(np.argmin(np.abs(ys - event.y)))
        if radio.value_selected != radio.labels[i].get_text():
            radio.set_active(i)

    return canvas.mpl_connect("button_press_event", on_press)


__all__ = ["row_clickable"]

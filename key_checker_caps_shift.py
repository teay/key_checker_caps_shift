import ctypes
import time
import sys

# โหลด user32.dll ซึ่งมีฟังก์ชัน GetAsyncKeyState และ GetKeyState
user32 = ctypes.WinDLL('user32', use_last_error=True)

# กำหนด Signature ของฟังก์ชัน GetAsyncKeyState
GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.argtypes = [ctypes.c_int]
GetAsyncKeyState.restype = ctypes.c_short

# กำหนด Signature ของฟังก์ชัน GetKeyState (ใช้สำหรับสถานะ Caps Lock และ Shift)
GetKeyState = user32.GetKeyState
GetKeyState.argtypes = [ctypes.c_int]
GetKeyState.restype = ctypes.c_short

# Global dictionary สำหรับติดตามสถานะของปุ่มเพื่อหลีกเลี่ยงการพิมพ์ซ้ำซ้อน
g_key_states = {vk_code: False for vk_code in range(256)}

# Virtual Key Codes สำหรับปุ่ม Modifier ที่เราสนใจ
VK_CAPITAL = 0x14  # Caps Lock key
VK_SHIFT = 0x10    # Shift key (any Shift)

# แผนผัง Virtual Key Codes กับชื่อภาษาไทยที่อ่านง่าย (ปรับปรุงจากเวอร์ชันก่อนหน้า)
# เพิ่มข้อมูลเกี่ยวกับสถานะของ Caps Lock และ Shift เข้าไปในชื่อปุ่มบางตัว
KEY_MAP_THAI = {
    0x01: "ปุ่มเมาส์ซ้าย (VK_LBUTTON)",
    0x02: "ปุ่มเมาส์ขวา (VK_RBUTTON)",
    0x03: "ปุ่ม Control-break (VK_CANCEL)",
    0x04: "ปุ่มเมาส์กลาง (VK_MBUTTON)",
    0x05: "ปุ่มเมาส์ X1 (VK_XBUTTON1)",
    0x06: "ปุ่มเมาส์ X2 (VK_XBUTTON2)",
    0x07: "สงวนไว้ (0x07)",
    0x08: "ปุ่ม Backspace (VK_BACK)",
    0x09: "ปุ่ม Tab (VK_TAB)",
    0x0A: "ไม่ได้กำหนด (0x0A)",
    0x0B: "ไม่ได้กำหนด (0x0B)",
    0x0C: "ปุ่ม Clear (VK_CLEAR)",
    0x0D: "ปุ่ม Enter (VK_RETURN)",
    0x0E: "ไม่ได้กำหนด (0x0E)",
    0x0F: "ไม่ได้กำหนด (0x0F)",
    0x10: "ปุ่ม Shift (VK_SHIFT)", # จะถูกจัดการแยกต่างหาก
    0x11: "ปุ่ม Ctrl (VK_CONTROL)",
    0x12: "ปุ่ม Alt (VK_MENU)",
    0x13: "ปุ่ม Pause (VK_PAUSE)",
    0x14: "ปุ่ม Caps Lock (VK_CAPITAL)", # จะถูกจัดการแยกต่างหาก
    0x15: "ปุ่ม IME Kana mode / Hangul (VK_KANA/HANGUL)",
    0x16: "ปุ่ม IME On (VK_IME_ON)",
    0x17: "ปุ่ม IME Junja mode (VK_JUNJA)",
    0x18: "ปุ่ม IME final mode (VK_FINAL)",
    0x19: "ปุ่ม IME Hanja mode / Kanji (VK_HANJA/KANJI)",
    0x1A: "ปุ่ม IME Off (VK_IME_OFF)",
    0x1B: "ปุ่ม Esc (VK_ESCAPE)",
    0x1C: "ปุ่ม IME convert (VK_CONVERT)",
    0x1D: "ปุ่ม IME nonconvert (VK_NONCONVERT)",
    0x1E: "ปุ่ม IME accept (VK_ACCEPT)",
    0x1F: "ปุ่ม IME mode change request (VK_MODECHANGE)",
    0x20: "ปุ่ม Spacebar (VK_SPACE)",
    0x21: "ปุ่ม Page up (VK_PRIOR)",
    0x22: "ปุ่ม Page down (VK_NEXT)",
    0x23: "ปุ่ม End (VK_END)",
    0x24: "ปุ่ม Home (VK_HOME)",
    0x25: "ปุ่มลูกศรซ้าย (VK_LEFT)",
    0x26: "ปุ่มลูกศรขึ้น (VK_UP)",
    0x27: "ปุ่มลูกศรขวา (VK_RIGHT)",
    0x28: "ปุ่มลูกศรลง (VK_DOWN)",
    0x29: "ปุ่ม Select (VK_SELECT)",
    0x2A: "ปุ่ม Print (VK_PRINT)",
    0x2B: "ปุ่ม Execute (VK_EXECUTE)",
    0x2C: "ปุ่ม Print screen (VK_SNAPSHOT)",
    0x2D: "ปุ่ม Insert (VK_INSERT)",
    0x2E: "ปุ่ม Delete (VK_DELETE)",
    0x2F: "ปุ่ม Help (VK_HELP)",
    # Numeric keys (0-9)
    ord('0'): "ปุ่ม 0 (0x30)", ord('1'): "ปุ่ม 1 (0x31)", ord('2'): "ปุ่ม 2 (0x32)",
    ord('3'): "ปุ่ม 3 (0x33)", ord('4'): "ปุ่ม 4 (0x34)", ord('5'): "ปุ่ม 5 (0x35)",
    ord('6'): "ปุ่ม 6 (0x36)", ord('7'): "ปุ่ม 7 (0x37)", ord('8'): "ปุ่ม 8 (0x38)",
    ord('9'): "ปุ่ม 9 (0x39)",
    0x3A: "ไม่ได้กำหนด (0x3A)", 0x3B: "ไม่ได้กำหนด (0x3B)", 0x3C: "ไม่ได้กำหนด (0x3C)",
    0x3D: "ไม่ได้กำหนด (0x3D)", 0x3E: "ไม่ได้กำหนด (0x3E)", 0x3F: "ไม่ได้กำหนด (0x3F)",
    0x40: "ไม่ได้กำหนด (0x40)",
    # Alphabet keys (A-Z)
    ord('A'): "ปุ่ม A (0x41)", ord('B'): "ปุ่ม B (0x42)", ord('C'): "ปุ่ม C (0x43)",
    ord('D'): "ปุ่ม D (0x44)", ord('E'): "ปุ่ม E (0x45)", ord('F'): "ปุ่ม F (0x46)",
    ord('G'): "ปุ่ม G (0x47)", ord('H'): "ปุ่ม H (0x48)", ord('I'): "ปุ่ม I (0x49)",
    ord('J'): "ปุ่ม J (0x4A)", ord('K'): "ปุ่ม K (0x4B)", ord('L'): "ปุ่ม L (0x4C)",
    ord('M'): "ปุ่ม M (0x4D)", ord('N'): "ปุ่ม N (0x4E)", ord('O'): "ปุ่ม O (0x4F)",
    ord('P'): "ปุ่ม P (0x50)", ord('Q'): "ปุ่ม Q (0x51)", ord('R'): "ปุ่ม R (0x52)",
    ord('S'): "ปุ่ม S (0x53)", ord('T'): "ปุ่ม T (0x54)", ord('U'): "ปุ่ม U (0x55)",
    ord('V'): "ปุ่ม V (0x56)", ord('W'): "ปุ่ม W (0x57)", ord('X'): "ปุ่ม X (0x58)",
    ord('Y'): "ปุ่ม Y (0x59)", ord('Z'): "ปุ่ม Z (0x5A)",
    0x5B: "ปุ่ม Windows ซ้าย (VK_LWIN)",
    0x5C: "ปุ่ม Windows ขวา (VK_RWIN)",
    0x5D: "ปุ่ม Application (VK_APPS)",
    0x5E: "สงวนไว้ (0x5E)",
    0x5F: "ปุ่ม Computer Sleep (VK_SLEEP)",
    # Numpad keys
    0x60: "ปุ่ม NumPad 0 (VK_NUMPAD0)", 0x61: "ปุ่ม NumPad 1 (VK_NUMPAD1)",
    0x62: "ปุ่ม NumPad 2 (VK_NUMPAD2)", 0x63: "ปุ่ม NumPad 3 (VK_NUMPAD3)",
    0x64: "ปุ่ม NumPad 4 (VK_NUMPAD4)", 0x65: "ปุ่ม NumPad 5 (VK_NUMPAD5)",
    0x66: "ปุ่ม NumPad 6 (VK_NUMPAD6)", 0x67: "ปุ่ม NumPad 7 (VK_NUMPAD7)",
    0x68: "ปุ่ม NumPad 8 (VK_NUMPAD8)", 0x69: "ปุ่ม NumPad 9 (VK_NUMPAD9)",
    0x6A: "ปุ่มคูณ (VK_MULTIPLY)",
    0x6B: "ปุ่มบวก (VK_ADD)",
    0x6C: "ปุ่มตัวคั่น (VK_SEPARATOR)",
    0x6D: "ปุ่มลบ (VK_SUBTRACT)",
    0x6E: "ปุ่มจุดทศนิยม (VK_DECIMAL)",
    0x6F: "ปุ่มหาร (VK_DIVIDE)",
    # Function keys (F1-F24)
    0x70: "ปุ่ม F1 (VK_F1)", 0x71: "ปุ่ม F2 (VK_F2)", 0x72: "ปุ่ม F3 (VK_F3)",
    0x73: "ปุ่ม F4 (VK_F4)", 0x74: "ปุ่ม F5 (VK_F5)", 0x75: "ปุ่ม F6 (VK_F6)",
    0x76: "ปุ่ม F7 (VK_F7)", 0x77: "ปุ่ม F8 (VK_F8)", 0x78: "ปุ่ม F9 (VK_F9)",
    0x79: "ปุ่ม F10 (VK_F10)", 0x7A: "ปุ่ม F11 (VK_F11)", 0x7B: "ปุ่ม F12 (VK_F12)",
    0x7C: "ปุ่ม F13 (VK_F13)", 0x7D: "ปุ่ม F14 (VK_F14)", 0x7E: "ปุ่ม F15 (VK_F15)",
    0x7F: "ปุ่ม F16 (VK_F16)", 0x80: "ปุ่ม F17 (VK_F17)", 0x81: "ปุ่ม F18 (VK_F18)",
    0x82: "ปุ่ม F19 (VK_F19)", 0x83: "ปุ่ม F20 (VK_F20)", 0x84: "ปุ่ม F21 (VK_F21)",
    0x85: "ปุ่ม F22 (VK_F22)", 0x86: "ปุ่ม F23 (VK_F23)", 0x87: "ปุ่ม F24 (VK_F24)",
    0x88: "สงวนไว้ (0x88)", 0x89: "สงวนไว้ (0x89)", 0x8A: "สงวนไว้ (0x8A)",
    0x8B: "สงวนไว้ (0x8B)", 0x8C: "สงวนไว้ (0x8C)", 0x8D: "สงวนไว้ (0x8D)",
    0x8E: "สงวนไว้ (0x8E)", 0x8F: "สงวนไว้ (0x8F)",
    0x90: "ปุ่ม Num Lock (VK_NUMLOCK)",
    0x91: "ปุ่ม Scroll Lock (VK_SCROLL)",
    0x92: "OEM เฉพาะ (0x92)", 0x93: "OEM เฉพาะ (0x93)", 0x94: "OEM เฉพาะ (0x94)",
    0x95: "OEM เฉพาะ (0x95)", 0x96: "OEM เฉพาะ (0x96)",
    0x97: "ไม่ได้กำหนด (0x97)", 0x98: "ไม่ได้กำหนด (0x98)", 0x99: "ไม่ได้กำหนด (0x99)",
    0x9A: "ไม่ได้กำหนด (0x9A)", 0x9B: "ไม่ได้กำหนด (0x9B)", 0x9C: "ไม่ได้กำหนด (0x9C)",
    0x9D: "ไม่ได้กำหนด (0x9D)", 0x9E: "ไม่ได้กำหนด (0x9E)", 0x9F: "ไม่ได้กำหนด (0x9F)",
    0xA0: "ปุ่ม Shift ซ้าย (VK_LSHIFT)",
    0xA1: "ปุ่ม Shift ขวา (VK_RSHIFT)",
    0xA2: "ปุ่ม Ctrl ซ้าย (VK_LCONTROL)",
    0xA3: "ปุ่ม Ctrl ขวา (VK_RCONTROL)",
    0xA4: "ปุ่ม Alt ซ้าย (VK_LMENU)",
    0xA5: "ปุ่ม Alt ขวา (VK_RMENU)",
    0xA6: "ปุ่ม Browser Back (VK_BROWSER_BACK)",
    0xA7: "ปุ่ม Browser Forward (VK_BROWSER_FORWARD)",
    0xA8: "ปุ่ม Browser Refresh (VK_BROWSER_REFRESH)",
    0xA9: "ปุ่ม Browser Stop (VK_BROWSER_STOP)",
    0xAA: "ปุ่ม Browser Search (VK_BROWSER_SEARCH)",
    0xAB: "ปุ่ม Browser Favorites (VK_BROWSER_FAVORITES)",
    0xAC: "ปุ่ม Browser Start and Home (VK_BROWSER_HOME)",
    0xAD: "ปุ่ม Volume Mute (VK_VOLUME_MUTE)",
    0xAE: "ปุ่ม Volume Down (VK_VOLUME_DOWN)",
    0xAF: "ปุ่ม Volume Up (VK_VOLUME_UP)",
    0xB0: "ปุ่ม Next Track (VK_MEDIA_NEXT_TRACK)",
    0xB1: "ปุ่ม Previous Track (VK_MEDIA_PREV_TRACK)",
    0xB2: "ปุ่ม Stop Media (VK_MEDIA_STOP)",
    0xB3: "ปุ่ม Play/Pause Media (VK_MEDIA_PLAY_PAUSE)",
    0xB4: "ปุ่ม Start Mail (VK_LAUNCH_MAIL)",
    0xB5: "ปุ่ม Select Media (VK_LAUNCH_MEDIA_SELECT)",
    0xB6: "ปุ่ม Start Application 1 (VK_LAUNCH_APP1)",
    0xB7: "ปุ่ม Start Application 2 (VK_LAUNCH_APP2)",
    0xB8: "สงวนไว้ (0xB8)", 0xB9: "สงวนไว้ (0xB9)",
    0xBA: "ปุ่ม OEM 1 (สำหรับ US ANSI: Semicolon and Colon key) (VK_OEM_1)",
    0xBB: "ปุ่ม OEM PLUS (สำหรับทุกประเทศ: Equals and Plus key) (VK_OEM_PLUS)",
    0xBC: "ปุ่ม OEM COMMA (สำหรับทุกประเทศ: Comma and Less Than key) (VK_OEM_COMMA)",
    0xBD: "ปุ่ม OEM MINUS (สำหรับทุกประเทศ: Dash and Underscore key) (VK_OEM_MINUS)",
    0xBE: "ปุ่ม OEM PERIOD (สำหรับทุกประเทศ: Period and Greater Than key) (VK_OEM_PERIOD)",
    0xBF: "ปุ่ม OEM 2 (สำหรับ US ANSI: Forward Slash and Question Mark key) (VK_OEM_2)",
    0xC0: "ปุ่ม OEM 3 (สำหรับ US ANSI: Grave Accent and Tilde key) (VK_OEM_3)",
    0xC1: "สงวนไว้ (0xC1)", 0xC2: "สงวนไว้ (0xC2)", 0xC3: "สงวนไว้ (0xC3)",
    0xC4: "สงวนไว้ (0xC4)", 0xC5: "สงวนไว้ (0xC5)", 0xC6: "สงวนไว้ (0xC6)",
    0xC7: "สงวนไว้ (0xC7)", 0xC8: "สงวนไว้ (0xC8)", 0xC9: "สงวนไว้ (0xC9)",
    0xCA: "สงวนไว้ (0xCA)", 0xCB: "สงวนไว้ (0xCB)", 0xCC: "สงวนไว้ (0xCC)",
    0xCD: "สงวนไว้ (0xCD)", 0xCE: "สงวนไว้ (0xCE)", 0xCF: "สงวนไว้ (0xCF)",
    0xD0: "สงวนไว้ (0xD0)", 0xD1: "สงวนไว้ (0xD1)", 0xD2: "สงวนไว้ (0xD2)",
    0xD3: "สงวนไว้ (0xD3)", 0xD4: "สงวนไว้ (0xD4)", 0xD5: "สงวนไว้ (0xD5)",
    0xD6: "สงวนไว้ (0xD6)", 0xD7: "สงวนไว้ (0xD7)", 0xD8: "สงวนไว้ (0xD8)",
    0xD9: "สงวนไว้ (0xD9)", 0xDA: "สงวนไว้ (0xDA)",
    0xDB: "ปุ่ม OEM 4 (สำหรับ US ANSI: Left Brace key) (VK_OEM_4)",
    0xDC: "ปุ่ม OEM 5 (สำหรับ US ANSI: Backslash and Pipe key) (VK_OEM_5)",
    0xDD: "ปุ่ม OEM 6 (สำหรับ US ANSI: Right Brace key) (VK_OEM_6)",
    0xDE: "ปุ่ม OEM 7 (สำหรับ US ANSI: Apostrophe and Double Quotation Mark key) (VK_OEM_7)",
    0xDF: "ปุ่ม OEM 8 (สำหรับ Canadian CSA: Right Ctrl key) (VK_OEM_8)",
    0xE0: "สงวนไว้ (0xE0)",
    0xE1: "OEM เฉพาะ (0xE1)",
    0xE2: "ปุ่ม OEM 102 (สำหรับ European ISO: Backslash and Pipe key) (VK_OEM_102)",
    0xE3: "OEM เฉพาะ (0xE3)", 0xE4: "OEM เฉพาะ (0xE4)",
    0xE5: "ปุ่ม IME PROCESS (VK_PROCESSKEY)",
    0xE6: "OEM เฉพาะ (0xE6)",
    0xE7: "ใช้ส่งอักขระ Unicode เสมือนการกดแป้นพิมพ์ (VK_PACKET)",
    0xE8: "ไม่ได้กำหนด (0xE8)",
    0xE9: "OEM เฉพาะ (0xE9)", 0xEA: "OEM เฉพาะ (0xEA)", 0xEB: "OEM เฉพาะ (0xEB)",
    0xEC: "OEM เฉพาะ (0xEC)", 0xED: "OEM เฉพาะ (0xED)", 0xEE: "OEM เฉพาะ (0xEE)",
    0xEF: "OEM เฉพาะ (0xEF)", 0xF0: "OEM เฉพาะ (0xF0)", 0xF1: "OEM เฉพาะ (0xF1)",
    0xF2: "OEM เฉพาะ (0xF2)", 0xF3: "OEM เฉพาะ (0xF3)", 0xF4: "OEM เฉพาะ (0xF4)",
    0xF5: "OEM เฉพาะ (0xF5)",
    0xF6: "ปุ่ม Attn (VK_ATTN)",
    0xF7: "ปุ่ม CrSel (VK_CRSEL)",
    0xF8: "ปุ่ม ExSel (VK_EXSEL)",
    0xF9: "ปุ่ม Erase EOF (VK_EREOF)",
    0xFA: "ปุ่ม Play (VK_PLAY)",
    0xFB: "ปุ่ม Zoom (VK_ZOOM)",
    0xFC: "สงวนไว้ (VK_NONAME)",
    0xFD: "ปุ่ม PA1 (VK_PA1)",
    0xFE: "ปุ่ม Clear (VK_OEM_CLEAR)"
}

def get_key_name_with_status(vk_code):
    """ส่งคืนชื่อปุ่มที่มนุษย์อ่านเข้าใจได้สำหรับ Virtual Key Code ที่กำหนด (ภาษาไทย)
    พร้อมสถานะของ Caps Lock และ Shift สำหรับปุ่มตัวอักษรและตัวเลข"""

    base_name = KEY_MAP_THAI.get(vk_code, f"ปุ่มไม่รู้จัก / ไม่ได้กำหนด (0x{vk_code:02X})")

    # ตรวจสอบสถานะของ Caps Lock (เปิด/ปิด)
    # GetKeyState bit 0 (0x0001) is set if the toggle key is ON.
    caps_lock_on = (GetKeyState(VK_CAPITAL) & 0x0001) != 0

    # ตรวจสอบว่าปุ่ม Shift ถูกกดอยู่หรือไม่
    # GetKeyState bit 15 (0x8000) is set if the key is currently pressed.
    shift_pressed = (GetKeyState(VK_SHIFT) & 0x8000) != 0

    # สำหรับปุ่มตัวอักษรและตัวเลข เราจะเพิ่มข้อมูลสถานะเข้าไป
    # ตรวจสอบช่วง VK codes ของตัวอักษรและตัวเลข
    if (ord('A') <= vk_code <= ord('Z')) or (ord('0') <= vk_code <= ord('9')):
        status_info = []
        if caps_lock_on:
            status_info.append("Caps Lock: เปิด")
        if shift_pressed:
            status_info.append("Shift: กดอยู่")
        
        if status_info:
            return f"{base_name} ({', '.join(status_info)})"
    
    # สำหรับปุ่มอื่นๆ หรือถ้าไม่เข้าเงื่อนไข จะคืนชื่อปกติ
    return base_name

def main():
    print("กำลังตรวจสอบสถานะ Virtual Key Codes ทั้งหมด (พร้อมสถานะ Caps Lock และ Shift)...")
    print("กดปุ่ม Esc (0x1B) เพื่อออกจากโปรแกรม")

    # Virtual Key Code สำหรับปุ่ม Esc
    VK_ESCAPE = 0x1B

    try:
        while True:
            # ตรวจสอบการกดปุ่ม Esc เพื่อออกจากโปรแกรม
            if (GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0:
                print("\nตรวจพบการกดปุ่ม Esc กำลังออกจากโปรแกรม...")
                break

            # วนลูปตรวจสอบ Virtual Key Codes ทั้งหมด (ตั้งแต่ 0x00 ถึง 0xFF)
            for vk_code in range(256):
                # ตรวจสอบว่าปุ่มกำลังถูกกดอยู่หรือไม่
                if (GetAsyncKeyState(vk_code) & 0x8000) != 0:
                    # ถ้าปุ่มนั้นยังไม่เคยถูกบันทึกว่ากดอยู่
                    if not g_key_states[vk_code]:
                        print(f"ปุ่มถูกกด: {get_key_name_with_status(vk_code)}")
                        g_key_states[vk_code] = True  # ทำเครื่องหมายว่ากำลังกดอยู่
                else:
                    # ถ้าปุ่มไม่ได้ถูกกดอยู่ แต่เคยถูกบันทึกว่ากดอยู่ก่อนหน้านี้
                    if g_key_states[vk_code]:
                        # หากต้องการดูเหตุการณ์ปล่อยปุ่มด้วย ให้เปิดคอมเมนต์บรรทัดด้านล่างนี้
                        # print(f"ปุ่มถูกปล่อย: {get_key_name_with_status(vk_code)}")
                        g_key_states[vk_code] = False  # ทำเครื่องหมายว่าถูกปล่อยแล้ว

            time.sleep(0.01) # ตรวจสอบทุก 10 มิลลิวินาที เพื่อการตอบสนองที่ดีขึ้น
    except KeyboardInterrupt:
        print("\nโปรแกรมถูกขัดจังหวะโดยผู้ใช้ (Ctrl+C) กำลังออกจากโปรแกรม...")
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()

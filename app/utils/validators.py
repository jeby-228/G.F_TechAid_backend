"""
資料驗證工具
"""
import re
from typing import Optional
from pydantic import validator

def validate_phone_number(phone: str) -> bool:
    """驗證台灣手機號碼格式"""
    # 台灣手機號碼格式：09xxxxxxxx
    pattern = r'^09\d{8}$'
    return bool(re.match(pattern, phone))

def validate_taiwan_id(id_number: str) -> bool:
    """驗證台灣身分證字號格式"""
    # 台灣身分證字號格式：A123456789
    if len(id_number) != 10:
        return False
    
    # 第一個字元必須是英文字母
    if not id_number[0].isalpha():
        return False
    
    # 第二個字元必須是1或2
    if id_number[1] not in ['1', '2']:
        return False
    
    # 後面8個字元必須是數字
    if not id_number[2:].isdigit():
        return False
    
    return True

def validate_coordinates(lat: float, lng: float) -> bool:
    """驗證經緯度座標是否在台灣範圍內"""
    # 台灣經緯度範圍（大致）
    # 緯度：21.9°N - 25.3°N
    # 經度：120.0°E - 122.0°E
    return (21.9 <= lat <= 25.3) and (120.0 <= lng <= 122.0)

class PhoneNumberValidator:
    """手機號碼驗證器"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('手機號碼必須是字串')
        
        if not validate_phone_number(v):
            raise ValueError('無效的手機號碼格式')
        
        return v

class CoordinatesValidator:
    """座標驗證器"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, dict):
            raise TypeError('座標必須是字典格式')
        
        if 'lat' not in v or 'lng' not in v:
            raise ValueError('座標必須包含 lat 和 lng 欄位')
        
        try:
            lat = float(v['lat'])
            lng = float(v['lng'])
        except (ValueError, TypeError):
            raise ValueError('座標必須是數字')
        
        if not validate_coordinates(lat, lng):
            raise ValueError('座標超出台灣範圍')
        
        return v
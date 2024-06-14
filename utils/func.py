import os
import io
import base64

from PIL import Image
from datetime import datetime

from utils.config import agent_config


def get_time() -> str: 
    """
    return the current date
    Returns:
        str: _description_
    """
    now = datetime.now()
    time_of_day = now.strftime('%Y-%m-%d')  # 格式化为年月日和小时
    if 5 <= now.hour < 12:
        time_of_day += ' morning'
    elif 13 <= now.hour < 18:
        time_of_day += ' afternoon'
    else:
        time_of_day += ' evening'
    return time_of_day 


def readFile(name):
    # get the path of the file
    with open(agent_config.get(name), 'r', encoding='utf-8') as file:
        return file.read()


def save_img(img_bytes):
    img = Image.open(img_bytes)
    save_path = os.path.join('app/tmp', "current_image.png") 
    img.save(save_path)
    return save_path


def img_base64(image_path):
    with Image.open(image_path) as img:
        # 原始图片格式
        format = img.format.lower()

        # 将图片转换为字节数据
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=format)  # 保存为原始格式
        img_byte_arr = img_byte_arr.getvalue()

        # 对字节数据进行base64编码
        img_base64 = base64.b64encode(img_byte_arr)
        img_base64_str = img_base64.decode('utf-8')  # 将字节数据转换为字符串
        return img_base64_str
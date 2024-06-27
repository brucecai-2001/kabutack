import os
import io
import base64
import csv

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
    
    
def save_to_csv(func_name, func_doc, csv_file):
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入头部信息，如果文件是新创建的
        if os.path.getsize(csv_file) == 0:
            writer.writerow(['func_name', 'func_doc'])
        # 写入函数名称和文档
        writer.writerow([func_name, func_doc])

def check_and_save_to_csv(func_name, func_doc):
    csv_file = 'core/tool/tools_doc.csv'
    # 检查CSV文件是否存在，如果不存在则创建
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['func_name', 'func_doc'])  # 写入头部信息

    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # 检查工具文档是否已在CSV中
            for row in reader:
                if row['func_name'] == func_name:
                    return False  # 工具已保存

            # 如果工具文档不在CSV中，保存到CSV
            save_to_csv(func_name, func_doc, csv_file)
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

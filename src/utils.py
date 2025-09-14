
import urllib3
from bs4 import BeautifulSoup
import shutil
from datetime import datetime ,timedelta
import re
from typing import Tuple
from typing import List
dmr_starting_week = "2025ww34"

def parse_workweek_to_date(re, ww_str: str) -> datetime:
    """
    把 w38 / ww38 / w38.1 / ww38.2 转换成 datetime。
    """
    # 补全格式，比如 w38 → w38.0
    print(f"caputured scrub_notes{ww_str}")
    if re.fullmatch(r"w{1,2}\d{2}", ww_str.lower()):
        ww_str = ww_str + ".0"

    match = re.match(r"w{1,2}(\d{2})\.(\d)", ww_str.lower())
    if not match:
        return None

    week, day = int(match.group(1)), int(match.group(2))

    week = week - 1  #for Intel calendar

    year = datetime.now().year
    weekday = day % 7    # .0 → 周日，.1 → 周一 ... +1 is for intel calendar
    date_str = f"{year} {week} {weekday}"
    return datetime.strptime(date_str, "%Y %W %w")         

def date_to_workweek( dt_str ):

    """
    把日期字符串 'YYYY-MM-DD HH:MM:SS.sss' 转换成 'YYYYwwWW' 格式
    例如: '2025-08-30 19:59:28.547' -> '2025ww35'
    """
    # 解析字符串为 datetime
    dt = datetime.strptime(dt_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
    
    # isocalendar() -> (ISO year, ISO week number, ISO weekday)
    iso_year, iso_week, _ = dt.isocalendar()
    
    # 格式化结果
    return f"{iso_year}ww{iso_week:02d}"




def week_to_dates(week_int: int) -> (datetime, datetime):
    """
    计算某年某周对应的起止日期（周日开始）
    week 格式: '33' 或 '2025-33'
    """
    week = str(week_int)
    if "-" in week:
        year, week_num = week.split("-")
        year = int(year)
        week_num = int(week_num)
    else:
        year = datetime.now().year
        week_num = int(week)

    # 找该年1月1日
    first_day = datetime(year, 1, 1)
    # 计算第一个周日
    days_to_sunday = (6 - first_day.weekday()) % 7
    first_sunday = first_day + timedelta(days=days_to_sunday)
    # 计算目标周的开始日期
    start_date = first_sunday + timedelta(weeks=week_num - 1 - 1) #last -1 is for intel clendar
    end_date = start_date + timedelta(days=6)
    return start_date, end_date


def parse_workweek(ww_str: str) -> Tuple[int, int]:
    """
    把 '2025ww34' 解析成 (year, week)
    """
    year = int(ww_str[:4])
    week = int(ww_str[-2:])
    return year, week

def get_missing_workweeks(current_ww: str, start_ww : str) -> List[str]:
    """
    返回 start_ww 和 current_ww 之间缺失的 workweeks（开区间，支持跨年，周日为锚点）
    """
    if start_ww == "" : 
       start_ww  = dmr_starting_week

    start_year, start_week = parse_workweek(start_ww)
    cur_year, cur_week = parse_workweek(current_ww)

    # 周日作为锚点
    start_date = datetime.fromisocalendar(start_year, start_week, 7)
    cur_date   = datetime.fromisocalendar(cur_year, cur_week, 7)

    if start_date >= cur_date:
        return []

    result = []
    wk_date = start_date + timedelta(weeks=1)
    while wk_date < cur_date:
        y, w, _ = wk_date.isocalendar()
        result.append(f"{y}ww{w:02d}")
        wk_date += timedelta(weeks=1)

    return result
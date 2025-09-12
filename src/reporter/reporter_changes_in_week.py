# reporter/reprter_changes_in_week.py
from .base_reporter import BaseReporter
import sighting_util as su
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime, timedelta
from  hsd_connection  import HSDConnection

class ReporterChangesInWeek(BaseReporter): 
 
    def __init__(self):
        super().__init__()  # 如果基类有初始化，建议调用
        descrption = ""

    def generate(self, sighting_list, week=36, **kwargs) -> Dict[str, List[List[Any]]]:

        '''
        import inspect
        print("DEBUG ReporterChangesInWeek from:", inspect.getfile(self.__class__))
        print("DEBUG generate signature:", inspect.signature(self.generate))
        '''

        self.sightings = sighting_list
        start_date, end_date = self.week_to_dates(week)
        self.week = str(week)
        # 定义7个结果表
        table1_opened = []
        table1_opened_dict = []
        
        table2_closed = []
        table2_closed_dict = []

        table3_transferred = []
        table3_transferred_dict = []
        
        table4_root_caused = []
        table4_root_caused_dict = []
        
        table5_implemented = []
        table5_implemented_dict = []

        table6_exposure_changed = []
        table6_exposure_changed_dict = []

        table7_forum_changed = []
        table7_forum_changed_dict = []
        default_headers = ["id", "title", "exposure", "status", "forum", "exposure"]

        # 辅助判断时间是否在周内
        def in_week(dt_str):
            if not dt_str:
                return False
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
            return start_date <= dt < end_date

        # placeholder函数，先返回空字符串，后续可改成业务函数
        def justification_placeholder(sighting_id, change_type):
            return ""


        # 遍历sightings做分类填表
        for s in self.sightings:
            o_hsd_conn= HSDConnection()
            o_hsd_conn.fetch_data(sighting_id = s, fetch_history=True, fetch_links=False, fetch_sets=False)
             
            sid = o_hsd_conn.get_sighting_field_value("id")
            forum = o_hsd_conn.get_sighting_field_value("forum")
            title = o_hsd_conn.get_sighting_field_value("title")
            exposure = o_hsd_conn.get_sighting_field_value("exposure")
            status = o_hsd_conn.get_sighting_field_value("status")
            status_reason = o_hsd_conn.get_sighting_field_value("status_reason")
            categorization = o_hsd_conn.get_sighting_field_value("categorization")
            scrub_note = o_hsd_conn.get_sighting_field_value("scrub_note")
            suspect_area = o_hsd_conn.get_sighting_field_value("suspect_area")
            ingredient = o_hsd_conn.get_sighting_field_value("ingredient")
            root_cause_desc = o_hsd_conn.get_sighting_field_value("root_cause_detail")

            # Table1: Opened last week (用 submitted_date 判断，字段名可能不同，替换为sighting_submitted_date)
            if in_week(  o_hsd_conn.get_sighting_field_value("sighting_submitted_date")):
                table1_opened_dict.append({
                    "Categorization": categorization,
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "Scrub Note or Executive Summary": scrub_note
                })

            '''
            if (table1_opened_dict): 
                headers = list(table1_opened_dict[0].keys())
                table1_opened = [headers] + [[row[h] for h in headers] for row in table1_opened_dict]
            else:   
                headers = default_headers
            '''

            # Table2: newly closed last week (complete reject) (closed_date)
            if in_week( o_hsd_conn.get_sighting_field_value("closed_date")):
                table2_closed_dict.append({
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "scrub note or executive summary": scrub_note
                })
            '''
            if(table2_closed_dict):
                headers = list(table2_closed_dict[0].keys())
                table2_closed = [headers] + [[row[h] for h in headers] for row in table2_closed_dict]
            else:
                 headers = default_headers
            '''
            #Table3: transferred last week (transferred_date)
            if in_week( o_hsd_conn.get_sighting_field_value("transferred_date")):
                table3_transferred_dict.append({
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "status": status,
                    "suspect Area": suspect_area,
                    "ingredient": ingredient,
                    "scrub Note": scrub_note
                })

            '''
            if table3_transferred_dict : 
                headers = list(table3_transferred_dict[0].keys())
                table3_transferred = [headers] + [[row[h] for h in headers] for row in table3_transferred_dict]
            else:
                headers = default_headers
            '''

            
            # Table4: root caused last week (root_caused_date)
            if in_week(o_hsd_conn.get_sighting_field_value("root_caused_date")) :
                table4_root_caused_dict.append({
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "status": status,
                    "root cause description": root_cause_desc
                })
            '''
                
            if table4_root_caused_dict: 
                headers = list(table4_root_caused_dict[0].keys())
                table4_root_caused = [headers] + [[row[h] for h in headers] for row in table4_root_caused_dict]
            else:
                headers = default_headers
            '''
            
            
            # Table5: implemented last week (implemented_date)
            if status == "implemented" and  in_week(o_hsd_conn.get_sighting_field_value("implemented_date")):
                table5_implemented_dict.append({
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "status": status,
                    "Root Cause Description": root_cause_desc
                })

            '''
            if table5_implemented_dict:
                headers = list(table5_implemented_dict[0].keys())
                table5_implemented = [headers] + [[row[h] for h in headers] for row in table5_implemented_dict]
            else:
                headers = default_headers
            '''

            # Table6: exposure changed last week
            history = o_hsd_conn.get_sighting_history()["data"]
            prev_exposure = None

            prev_forum = None
            exposure_changes = []
            forum_changes = []

            # 按时间排序（用 updated_date 而不是 timestamp）
            for rev in sorted(history, key=lambda r: r['updated_date']):
                ts = datetime.strptime(rev['updated_date'], "%Y-%m-%d %H:%M:%S.%f")
                exposure_curr = rev.get("bug.exposure") 
                forum_curr = rev.get("bug.forum")
                # 如果当前记录在目标时间范围内
                if start_date <= ts <= end_date:
                    if prev_exposure is not None and exposure_curr != prev_exposure:
                        exposure_changes.append(f"from {prev_exposure} --> to {exposure_curr};") 

                    if prev_forum is not None and forum_curr != prev_forum:
                        forum_changes.append(f"from {prev_forum} --> to {forum_curr}")     

                # 每次都更新 prev_exposure，不论是否在时间范围内
                prev_exposure = exposure_curr
                prev_forum = forum_curr

            if exposure_changes:
                table6_exposure_changed_dict.append({
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "Status Changed": "; ".join(exposure_changes),
                    "Justification": justification_placeholder(sid, "exposure")
                })



            if forum_changes:
                table7_forum_changed_dict.append({
                    "Forum": forum,
                    "ID": sid,
                    "Title": title,
                    "Exposure": exposure,
                    "Forum Change": "; ".join(forum_changes),
                    "Justification": justification_placeholder(sid, "forum")
                })

            '''
            # 生成表格
            if table6_exposure_changed_dict:
                headers = list(table6_exposure_changed_dict[0].keys()) if table6_exposure_changed_dict else []
                table6_exposure_changed = [headers] + [[row[h] for h in headers] for row in table6_exposure_changed_dict]
            else:
                headers= default_headers

            if     table7_forum_changed_dict : 
                headers = list(table7_forum_changed_dict.keys())
                table7_forum_changed = [headers] + [[row[h] for h in headers] for row in table7_forum_changed_dict]

            else:
                headers= default_headers

            '''


        # Table0: overall summary（数目统计）
        table0_overall_dict = [{
            "Opened": len(table1_opened_dict),
            "Closed": len(table2_closed_dict),
            "Transferred": len(table3_transferred_dict),
            "Root Caused": len(table4_root_caused_dict),
            "Implemented": len(table5_implemented_dict),
            "Exposure Changed": len(table6_exposure_changed_dict),
            "Forum Changed": len(table7_forum_changed_dict),
            "Week": week,
            "Start Date": start_date.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d")
        }]


        '''
        headers = list(table0_overall_dict.keys())
        rows = [table0_overall_dict[h] for h in headers]
        table0_overall = [headers, rows]
        '''
        self.update_description()
        print(f"Debug table {table0_overall_dict}")
        return {
            "table0_overall_update_summary": table0_overall_dict,
            "table1_opened": table1_opened_dict,
            "table2_closed": table2_closed_dict,
            "table3_transferred": table3_transferred_dict,
            "table4_root_caused": table4_root_caused_dict,
            "table5_implemented": table5_implemented_dict,
            "table6_exposure_changed": table6_exposure_changed_dict,
            "table7_forum_changed": table7_forum_changed_dict,
        }
    def update_description(self): 
        self.descrption = f"This is to report what were changed in WW{self.week}"

    def get_description(self):
        return self.descrption
    
    def week_to_dates(self, week_int: int) -> (datetime, datetime):
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


     

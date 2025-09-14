# reporter/reprter_changes_in_week.py
from .base_reporter import BaseReporter
import sighting_util as su
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime, timedelta
from  hsd_connection  import HSDConnection
import utils  as u
from concurrent.futures import ThreadPoolExecutor, as_completed


class ReporterChangesInWeek(BaseReporter): 
 
    def __init__(self):
        super().__init__()  # 如果基类有初始化，建议调用
        descrption = ""
        self.table1_opened_list = [] 
        self.table2_closed_list = []
        self.table3_transferred_list = []
        self.table4_root_caused_list = []
        self.table5_implemented_list = []
        self.table6_exposure_changed_list = []
        self.table7_forum_changed_list = []
        self.table0_overall_list = []



    '''to be used by multithreads to improve the efficency    
    '''
    def _process_sighting(self, s, start_date, end_date):
        """
        返回该 sighting 的所有表格信息（dict of dicts）
        """
        o_hsd_conn = HSDConnection()
        o_hsd_conn.fetch_data(
            sighting_id=s,
            fetch_history=True,
            fetch_links=False,
            fetch_sets=False
        )

        sid = o_hsd_conn.get_sighting_field_value("id")
        forum = o_hsd_conn.get_sighting_field_value("forum")
        title = o_hsd_conn.get_sighting_field_value("title")
        exposure = o_hsd_conn.get_sighting_field_value("exposure")
        status = o_hsd_conn.get_sighting_field_value("status")
        categorization = o_hsd_conn.get_sighting_field_value("categorization")
        scrub_note = o_hsd_conn.get_sighting_field_value("scrub_note")
        suspect_area = o_hsd_conn.get_sighting_field_value("suspect_area")
        ingredient = o_hsd_conn.get_sighting_field_value("ingredient")
        root_cause_desc = o_hsd_conn.get_sighting_field_value("root_cause_detail")
        report_type = o_hsd_conn.get_sighting_field_value("report_type")

        # 如果是 presighting，直接跳过
        if report_type == "presighting":
            return None

        # 辅助函数判断时间是否在周内
        def in_week(dt_str):
            if not dt_str:
                return False
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
            return start_date <= dt < end_date

        # placeholder
        def justification_placeholder(sighting_id, change_type):
            return ""


        # Table1: Opened
        if in_week(o_hsd_conn.get_sighting_field_value("sighting_submitted_date")):
            self.table1_opened_list.append({
                    "Categorization": categorization,
                    "forum": forum,
                    "id": sid,
                    "title": title,
                    "exposure": exposure,
                    "Scrub Note or Executive Summary": scrub_note
                })

        # Table2: Closed
        if in_week(o_hsd_conn.get_sighting_field_value("closed_date")):
            self.table2_closed_list.append({
                "forum": forum,
                "id": sid,
                "title": title,
                "exposure": exposure,
                "scrub note or executive summary": scrub_note
            })

        # Table3: Transferred
        if in_week(o_hsd_conn.get_sighting_field_value("transferred_date")):
            self.table3_transferred_list.append({
                "forum": forum,
                "id": sid,
                "title": title,
                "exposure": exposure,
                "status": status,
                "suspect Area": suspect_area,
                "ingredient": ingredient,
                "scrub_Note": scrub_note
            })
        # Table4: Root Caused
        if in_week(o_hsd_conn.get_sighting_field_value("root_caused_date")):
            self.table4_root_caused_list.append({
                "forum": forum,
                "id": sid,
                "title": title,
                "exposure": exposure,
                "status": status,
                "root_cause_detail": root_cause_desc
            })

        # Table5: Implemented
        if status == "implemented" and in_week(o_hsd_conn.get_sighting_field_value("implemented_date")):
            self.table5_implemented_list.append({
                "forum": forum,
                "id": sid,
                "title": title,
                "exposure": exposure,
                "status": status,
                "root_cause_detail": root_cause_desc
            })

        # Table6/7: Exposure & Forum changes
        history = o_hsd_conn.get_sighting_history()["data"]
        prev_exposure = None
        prev_forum = None
        exposure_changes = []
        forum_changes = []

        for rev in sorted(history, key=lambda r: r['updated_date']):
            ts = datetime.strptime(rev['updated_date'], "%Y-%m-%d %H:%M:%S.%f")
            exposure_curr = rev.get("bug.exposure")
            forum_curr = rev.get("bug.forum")

            if start_date <= ts <= end_date:
                if prev_exposure is not None and exposure_curr != prev_exposure:
                    exposure_changes.append(f"from {prev_exposure} --> to {exposure_curr};")
                if prev_forum is not None and forum_curr != prev_forum:
                    forum_changes.append(f"from {prev_forum} --> to {forum_curr}")

            prev_exposure = exposure_curr
            prev_forum = forum_curr

        if exposure_changes:
            self.table6_exposure_changed_list.append({
                "forum": forum,
                "id": sid,
                "title": title,
                "exposure": exposure,
                "status_changed": "; ".join(exposure_changes),
                "justification": justification_placeholder(sid, "exposure")
            })

        if forum_changes:
            self.table7_forum_changed_list.append({
                "forum": forum,
                "id": sid,
                "title": title,
                "exposure": exposure,
                "forum_changed": "; ".join(forum_changes),
                "justification": justification_placeholder(sid, "forum")
            })

        return True







    def generate(self, sighting_list, week=36, **kwargs) -> Dict[str, List[List[Any]]]:

        '''
        import inspect
        print("DEBUG ReporterChangesInWeek from:", inspect.getfile(self.__class__))
        print("DEBUG generate signature:", inspect.signature(self.generate))
        '''

        self.sightings = sighting_list
        start_date, end_date = u.week_to_dates(week)
        self.week = str(week)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(self._process_sighting, s, start_date, end_date) for s in self.sightings]
            #no result to be checked



        # Table0: overall summary（数目统计）
        self.table0_overall_list = [{
            "Opened": len(self.table1_opened_list),
            "Closed": len(self.table2_closed_list),
            "Transferred": len(self.table3_transferred_list),
            "Root Caused": len(self.table4_root_caused_list),
            "Implemented": len(self.table5_implemented_list),
            "Exposure Changed": len(self.table6_exposure_changed_list),
            "Forum Changed": len(self.table7_forum_changed_list),
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
        print(f"Debug table {self.table0_overall_list}")
        return {
            "table0_overall_update_summary": self.table0_overall_list ,
            "table1_opened": self.table1_opened_list,
            "table2_closed": self.table2_closed_list,
            "table3_transferred": self.table3_transferred_list,
            "table4_root_caused": self.table4_root_caused_list,
            "table5_implemented": self.table5_implemented_list,
            "table6_exposure_changed": self.table6_exposure_changed_list,
            "table7_forum_changed": self.table7_forum_changed_list,
        }
    def update_description(self): 
        self.descrption = f"This is to report what were changed in WW{self.week}"

    def get_description(self):
        return self.descrption
    



     

from .base_reporter import BaseReporter
import sighting_util as su
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime, timedelta
from  hsd_connection  import HSDConnection

class ReporterSightingListWithColumns(BaseReporter): 
 
    def __init__(self):
        super().__init__()  # 如果基类有初始化，建议调用
        self.descrption = "Sighting Report"

    def generate(self, sighting_list, week=None, **kwargs) -> Dict[str, List[List[Any]]]:
        self.sightings = sighting_list
        result_table = []
        print("reporter: sighting list with columns to run")
        for s in self.sightings:
            o_hsd_conn = HSDConnection()
            o_hsd_conn.fetch_data(sighting_id=s, fetch_history=True, fetch_comments=True, fetch_links=False, fetch_sets=False)

            sid = o_hsd_conn.get_sighting_field_value("id")
            forum = o_hsd_conn.get_sighting_field_value("forum")
            title = o_hsd_conn.get_sighting_field_value("title")
            exposure = o_hsd_conn.get_sighting_field_value("exposure")
            status = o_hsd_conn.get_sighting_field_value("status")
            status_reason = o_hsd_conn.get_sighting_field_value("status_reason")
            suspect_area = o_hsd_conn.get_sighting_field_value("suspect_area")
            days_no_comment =  o_hsd_conn.get_days_no_comment()
            report_type = o_hsd_conn.get_sighting_field_value("report_type")
            print(f" {s} is report_type of {report_type}")
            result_table.append({
                "id": sid,
                "title": title,
                "forum": forum,
                "exposure": exposure,
                "status": status,
                "status_reason": status_reason,
                "suspect_area": suspect_area,
                "report_type": report_type,
                "days_no_substantial_update": days_no_comment,
            })

        return {"result": result_table}


    def get_description(self): 
        return self.descrption

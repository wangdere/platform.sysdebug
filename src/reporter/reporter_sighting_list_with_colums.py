from .base_reporter import BaseReporter
import sighting_util as su
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime, timedelta
from  hsd_connection  import HSDConnection
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from datetime import datetime
import re

class ReporterSightingListWithColumns(BaseReporter): 
 
    def __init__(self):
        super().__init__()  # 如果基类有初始化，建议调用

        self.allowed_suspect_area = ["silicon", "system_boards", "os_driver","io_device", "bios","bmc_fw","CPLD", "PLD_fw", \
                                    "operating_system",  "platform.simics", "DDR5 DIMM", \
                                    "documentation", "script", "tool", "unknown"]
        self.descrption = f"Check days_no_update, owner, suspect area\n" \
                         +f"allowed suspect area:  {self.allowed_suspect_area}"
        self.result_table = []
        
    def generate(self, sighting_list, week=None, **kwargs) -> Dict[str, List[List[Any]]]:
        self.sightings = sighting_list
        
        print("reporter: sighting list with columns to run")

        # 开多线程跑
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self.process_sighting, s) for s in self.sightings]
#            for future in as_completed(futures):
#                result_table.append(future.result())


        # 保存结果为Excel ===
        
        if self.result_table:
            df = pd.DataFrame(self.result_table)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 清理隐藏字符，避免 Excel 乱码
            df = df.applymap(lambda x: re.sub(r'[\u200B-\u200D\uFEFF]', '', x) if isinstance(x, str) else x)

            filename = f"sighting_report_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            print(f"✅ Report saved to {filename}")

            return {"result": self.result_table}

    def process_sighting(self, s):
            o_hsd_conn = HSDConnection()
            o_hsd_conn.fetch_data(
                sighting_id=s,
                fetch_history=True,
                fetch_comments=True,
                fetch_links=False,
                fetch_sets=True
            )

            sid = o_hsd_conn.get_sighting_field_value("id")
            forum = o_hsd_conn.get_sighting_field_value("forum")
            forum = forum.replace(".", ".\u200B")
            title = o_hsd_conn.get_sighting_field_value("title")
            exposure = o_hsd_conn.get_sighting_field_value("exposure")
            status = o_hsd_conn.get_sighting_field_value("status")
            status_reason = o_hsd_conn.get_sighting_field_value("status_reason")
            suspect_area = o_hsd_conn.get_sighting_field_value("suspect_area")
            days_no_comment = o_hsd_conn.get_days_no_comment()
            report_type = o_hsd_conn.get_sighting_field_value("report_type")
            trans_team_found,trans_conclusion, trans_status, trans_tenant, refined_ingredient , trans_priority = o_hsd_conn.get_refined_ingredient()

            if (report_type == "sighting" ):
                sighting_submitted_date = o_hsd_conn.get_sighting_field_value("sighting_submitted_date")  #this must exist
                sighting_transferred_date = o_hsd_conn.get_sighting_field_value("transferred_date")  #may be null
                sighting_root_caused_date = o_hsd_conn.get_sighting_field_value("root_caused_date")  #may be null
                #sighting_implemented_date = o_hsd_conn.get_sighting_field_value("implemented_date")  #may be null
                sighting_closed_date = o_hsd_conn.get_sighting_field_value("closed_date")  #may be null
 
                time_to_transferred_days = self.calc_days_to_submitted_date(sighting_submitted_date,sighting_transferred_date )
                time_to_root_caused_days = self.calc_days_to_submitted_date(sighting_submitted_date,sighting_root_caused_date )
                #time_to_implemented_days = self.calc_days_to_submitted_date(sighting_submitted_date,sighting_implemented_date )
                time_to_closed_days=self.calc_days_to_submitted_date(sighting_submitted_date,sighting_closed_date )
            else:
                time_to_closed_days = 0
            
            warning_msg = ""
            warrning_count = 0

            owner = o_hsd_conn.get_sighting_field_value("owner")

            if owner == "":
                warrning_count += 1
                warning_msg += f"\n{warrning_count}: no owner"

            if suspect_area not in self.allowed_suspect_area:
                warrning_count += 1
                warning_msg += f"\n{warrning_count}: suspect_area={suspect_area or 'null'} should be in allowed list"

            if warrning_count == 0:
                warning_msg = "pass"


            #check the suspect_area vs. sets

            temp_result , temp_msg= self.check_bios_bugeco_sighting_central_validity(o_hsd_conn)
            if temp_result == False:
                warrning_count += 1
                warning_msg = f"\n{warrning_count}: " + temp_msg
            #generated df and save, file name is the timestamp of the generated. 


            
            return self.result_table.append({
                    "id": sid,
                    "title": title,
                    "forum": forum,
                    "exposure": exposure,
                    "status": status,
                    "status_reason": status_reason.replace(".", ".\u200B"),
                    "suspect_area": suspect_area.replace(".", ".\u200B"),
                    "report_type": report_type,
                    "days_no_substantial_update".replace("_", "_\u200B"): days_no_comment,
                    "warning": warning_msg,
                    "trans_tenant": trans_tenant,
                    "trans_status": trans_status,
                    "trans_team_found": trans_team_found,
                    "refined_ingredient": refined_ingredient,
                    "trans_conclusion": trans_conclusion,
                    "trans_priority": trans_priority,
                    "time_to_transferred_days": time_to_transferred_days,
                    "time_to_root_caused_days": time_to_root_caused_days,
                    "time_to_closed_days": time_to_closed_days

                })
    
    def get_description(self): 
        return self.descrption

    def check_bios_bugeco_sighting_central_validity(self, o_hsdconn ):
        sighting_id = o_hsdconn.get_sighting_field_value("id")
        title = o_hsdconn.get_sighting_field_value("title")
        is_silicon_sighting = su.is_a_silicon_sighting(o_hsdconn)
        is_bios_sighting = su.is_a_bios_sighting(o_hsdconn)
        is_silicon_solution_in_sets =  su.is_silicon_solution_in_sets(o_hsdconn)
        is_bios_solution_in_sets = su.is_bios_solution_in_sets(o_hsdconn)

                        
        if is_silicon_sighting  and not is_silicon_solution_in_sets:

            print(f"WARNING: Cant find  silicon solution, check suspect area and sets for {sighting_id}: {title}")
            msg = f"no silicon link in set"

            #print( self.msg)
            result = False
            
        elif is_bios_sighting and not is_bios_solution_in_sets:
            print(f"WARNING: Cant find  bios solution, check suspect area and sets for {sighting_id}: {title}")
            msg = f"no bios link in set"
            result = False
        elif not is_silicon_sighting  and not is_bios_sighting and \
                (is_silicon_solution_in_sets or is_bios_solution_in_sets ):
            print(f"WARNING: found bios or silicon solution  check suspect area and sets  {sighting_id}: {title}")
            msg = f"suspect is neither bios nor silicon "
            result = False
        else:
            print(f"Info: Pass the link check:  {sighting_id}: {title}")
            msg = f"pass"
            result = True
        # how to judget the suspect area and bugeco has the same code? 
        return  result, msg 
        #Then to check if sighting_central in the sets or not. 


    def calc_days_to_submitted_date(self,start_str, end_str):
        print (f" start : {start_str}, end: {end_str}")
        if not start_str or not end_str:
            return None
        
        fmt = "%Y-%m-%d %H:%M:%S.%f"
        start = datetime.strptime(start_str, fmt)
        end = datetime.strptime(end_str, fmt)

        #return (end - start).total_seconds() / 86400
        
        days = (end - start).days
        if days < 0 : 
            return None
        return days
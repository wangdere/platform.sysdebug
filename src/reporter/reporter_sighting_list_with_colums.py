from .base_reporter import BaseReporter
import sighting_util as su
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime, timedelta
from  hsd_connection  import HSDConnection
from concurrent.futures import ThreadPoolExecutor, as_completed


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
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.process_sighting, s) for s in self.sightings]
#            for future in as_completed(futures):
#                result_table.append(future.result())

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
                    "status_reason": status_reason.replace(".", "_\u200B"),
                    "suspect_area".replace("_", "_\u200B"): suspect_area,
                    "report_type": report_type,
                    "days_no_substantial_update".replace("_", "_\u200B"): days_no_comment,
                    "warning": warning_msg,
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
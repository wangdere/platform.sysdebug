# checker/rule_note_check.py
from .base_checker import BaseChecker
import sighting_util as su
from typing import Optional, List, Dict, Tuple

class RuleLinksCheck(BaseChecker): 
     #exception list to handle the  complext cases
    EXCEPTION_LIST = {
        #GNR
        "15015929631": "Errata in errata_central: '14022478850'",
        "16019608404": "silicon bug but WA by Val Tool.",
        # 你可以继续添加其他 ID 映射
        #DMR
        "14022517525": "It tracks OS issue,  with the other BIOS issue 14022825153 to as full fix, but BIOS remainsin the sets"
    }
 
    def __init__(self):
        self.o_hsdconn= None
        self.rule_name = "Check if suspect area/ingrdient comply with the sighting linkage and sets"
  

    def get_exception_info(self, sighting_id: str) -> Optional[str]:
        return self.EXCEPTION_LIST.get(sighting_id)

    def run(self, o_hsdconn):
        self.o_hsdconn = o_hsdconn
        self.result = False

        sighting_id = o_hsdconn.sighting_id
        title = self.o_hsdconn.get_sighting_field_value("title")
        #first to check if this is reviewed in the exception.
        exception_msg = self.get_exception_info(sighting_id)
        if exception_msg:
            self.msg =self.msg_short= f"✅ Info: Pass check with exception {exception_msg}:  {sighting_id}: {title}"
            self.result = True 
            return  self.result, self.msg 

        # 否则，执行正常检查逻辑
        return self.check_bios_bugeco_sighting_central_validity()
    

    def check_bios_bugeco_sighting_central_validity(self):
        sighting_id = self.o_hsdconn.get_sighting_field_value("id")
        title = self.o_hsdconn.get_sighting_field_value("title")
        is_silicon_sighting = su.is_a_silicon_sighting(self.o_hsdconn)
        is_bios_sighting = su.is_a_bios_sighting(self.o_hsdconn)
        is_silicon_solution_in_sets =  su.is_silicon_solution_in_sets(self.o_hsdconn)
        is_bios_solution_in_sets = su.is_bios_solution_in_sets(self.o_hsdconn)

                        
        if is_silicon_sighting  and not is_silicon_solution_in_sets:

            print(f"WARNING: Cant find  silicon solution, check suspect area and sets for {sighting_id}: {title}")
            self.msg = f"WARNING: Cant find  silicon solution"

            #print( self.msg)
            self.result = False
            
        elif is_bios_sighting and not is_bios_solution_in_sets:
            print(f"WARNING: Cant find  bios solution, check suspect area and sets for {sighting_id}: {title}")
            self.msg = f"WARNING: Cant find bios solution"
            #print(self.msg)
            self.result = False
        elif not is_silicon_sighting  and not is_bios_sighting and \
                (is_silicon_solution_in_sets or is_bios_solution_in_sets ):
            print(f"WARNING: found bios or silicon solution  check suspect area and sets  {sighting_id}: {title}")
            self.msg = f"WARNOING: found the solution is from bios or silicon "
            #print(self.msg)
            self.result = False
        else:
            print(f"Info: Pass the link check:  {sighting_id}: {title}")
            self.msg = f"Info: Pass the link check:"
            self.result = True
        # how to judget the suspect area and bugeco has the same code? 
        return  self.result, self.msg 
        #Then to check if sighting_central in the sets or not. 
# checker/rule_note_check.py
from .base_checker import BaseChecker

class RuleNoteCheck(BaseChecker):

    def __init__(self):
        self.o_hsdconn= None
        self.rule_name = "Check owner, suspect_area"
        self.msg ="Warning: "
        self.err_count = 0
        self.allowd_suspect_area = ["silicon", "system_boards", "os_driver","io_device", "bios","bmc_fw","cpld_fw", "cpld_pfr", \
                                    "operating_system",  "platform.simics", "DDR5 DIMM", \
                                    "documentation", "script", "tool", "unknown"]

    def run(self, o_hsdconn):
        '''
        note = sighting.fields.get("private.note", "")
        if not note:
            return False, "Missing private.note"
        '''
        self.err_count = 0
        #assumption is the o_hsdconn object has fetched the data. 
        print("run check note")
        self.o_hsdconn = o_hsdconn
        sighting_id = self.o_hsdconn.get_sighting_field_value("id")
        title = self.o_hsdconn.get_sighting_field_value("title")
        owner = self.o_hsdconn.get_sighting_field_value("owner")
        forum = self.o_hsdconn.get_sighting_field_value("forum")
        suspec_area = self.o_hsdconn.get_sighting_field_value("suspect_area")
        self.msg =f"Warning: {sighting_id} : "

        #orphan Sysdebug.platform  warn that if this sighting need to be debugged by platform system debug
        #multiple forum, if "Sysdebug.platform" co-exists with "Sysdebug.platform.xxx", then remove the "Sysdebug.platform"
        #owner check
        if owner == "" :
            self.err_count  = self.err_count  +1
            self.msg = self.msg + "\n" + str( self.err_count ) + f": no owner"

        if suspec_area not in self.allowd_suspect_area :
            self.err_count  = self.err_count  +1
            self.msg = self.msg + "\n" + str(self.err_count) + f": suspect_area={suspec_area} should be in {self.allowd_suspect_area}"
        
        if self.err_count == 0: 
            self.result = True
            self.msg = f"pass owner/suspect_area check"
        else:
            self.result = False

        return  self.result, self.msg 
        

       
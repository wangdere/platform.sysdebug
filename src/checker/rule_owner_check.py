# checker/rule_note_check.py
from .base_checker import BaseChecker

class RuleNoteCheck(BaseChecker):

    def __init__(self):
        self.o_hsdconn= None
        self.rule_name = "Check if a sighting has assigned with the correct owner"

    def run(self, o_hsdconn):
        '''
        note = sighting.fields.get("private.note", "")
        if not note:
            return False, "Missing private.note"
        '''

        #assumption is the o_hsdconn object has fetched the data. 
        print("run check note")
        self.o_hsdconn = o_hsdconn
        sighting_id = self.o_hsdconn.get_sighting_field_value("id")
        title = self.o_hsdconn.get_sighting_field_value("title")
        owner = self.o_hsdconn.get_sighting_field_value("owner")
        if owner :
            self.result = True
            self.msg = f"Info: Pass the owner  check: owner: {owner}  {sighting_id}: {title}"

        return  self.result, self.msg 
        
       
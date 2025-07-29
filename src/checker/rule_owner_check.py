# checker/rule_note_check.py
from .base_checker import BaseChecker

class RuleNoteCheck(BaseChecker):
    def run(self, o_HSDConnection):
        '''
        note = sighting.fields.get("private.note", "")
        if not note:
            return False, "Missing private.note"
        '''
        print("run check note")
        return True, "Note exists"
        
       
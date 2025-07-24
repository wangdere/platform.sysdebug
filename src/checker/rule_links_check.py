# checker/rule_note_check.py
from .base_checker import BaseChecker

class RuleLinksCheck(BaseChecker): 
    
    def __init__(self):
        self.o_hsdconn= None

    def run(self, o_hsdconn):
        self.o_hsdconn = o_hsdconn
        self.result = False
        self.msg = None
        '''
        note = sighting.fields.get("private.note", "")
        if not note:
            return False, "Missing private.note"
        '''
        sighting_id = o_hsdconn.sighting_id
        self.check_bios_bugeco_sighting_central_validity(sighting_id , o_hsdconn.get_sighting_sets_json(sighting_id), o_hsdconn.get_sighting_json(sighting_id) )

        return  self.result, self.msg 
        


    def check_bios_bugeco_sighting_central_validity(self,sighting_id, sets_data, parm_Json):

        
        ingredient = parm_Json.get("data", [])[0].get(self.o_hsdconn.get_full_field_name("ingredient"))
        if not ingredient:
            ingredient = "N.A"
        suspect_area = parm_Json.get("data", [])[0].get(self.o_hsdconn.get_full_field_name("suspect_area"))
        if not suspect_area:
            suspect_area = "N.A"
        
        title = parm_Json.get("data", [])[0].get(self.o_hsdconn.get_full_field_name("title"))
        print('Platform sighitng ID: ' + sighting_id + " Ingredient: " + ingredient +" suspect_area: " + suspect_area)

        found_bugeco = False
        found_sighting_cental = False
        found_central_fw = False

        for item in sets_data['data']:
            subject = item.get("subject", "").lower()
            tenant = item.get("tenant", "").lower()
            if( "slicon" in suspect_area or "silicon" in ingredient ):
    
                if "bugeco" in subject:
                    found_bugeco = True
                    item.get("component", "").lower()
                    print("found_bugeco for silion sighting:  " + item.get("id") + " with component" + item.get("component", ""))

                if "sighting_central" in tenant:
                    found_sighting_cental = True
                    item.get("component", "").lower()
                    print("found_sighting central for silicon sighting: " + item.get("id") + " with component" + item.get("component", ""))


            elif ("bios" in suspect_area or "bios" in ingredient):
                if "central_firmware" in tenant:
                    found_central_fw = True
                    item.get("component", "").lower()
                    print("found_bios for bios sighitng: " + item.get("id") + " with component:" + item.get("component", "")     )

            else: # this is for non-bios and non=slicon sighting
                #then check if any bugeco in the non-silicon sighting.
                if "bugeco" in subject or "sighting_central" in tenant or "central_firmware" in tenant:
                    self.result = False
                    self.msg = f"Found Warning for {sighting_id} "
                    print(f"⚠️ WARNING: Found bugEco/sighting_central/central_fw in subject  for non_silicon and non_BIOS ID: {sighting_id}  {item.get('title','')}")

        if ("slicon" in suspect_area or "silicon" in ingredient ) and not found_bugeco:
            print(f"⚠️ WARNING: Cant find  bugEco for  silicon sighting  {sighting_id} {title}" )
            self.result = False
            self.msg = f"Found Warning for {sighting_id} "
        elif ("slicon" in suspect_area or "silicon" in ingredient ) and not  found_sighting_cental:
            print(f"⚠️ WARNING: Cant find sighting central for  silicon sighting  {sighting_id } {title}" )
            self.result = False
            self.msg = f"Found Warning for {sighting_id} "
        elif ("bios" in suspect_area or "bios" in ingredient) and not found_central_fw:
            print(f"⚠️ WARNING: Cant find  central firmware for BIOS sighting  {sighting_id} {title}")
            self.result = False
            self.msg = f"Found Warning for {sighting_id} "
        else:
            print(f"✅ Info: Pass the link check for: " + sighting_id )
            self.result = True
            self.msg = f"Pass check for {sighting_id} "
        # how to judget the suspect area and bugeco has the same code? 

        #Then to check if sighting_central in the sets or not. 
import requests
from requests_kerberos import HTTPKerberosAuth
import json
import pandas as pd
import argparse
from  hsd_connection  import HSDConnection
from checker import base_checker
from reporter import base_reporter
import pkgutil
import importlib
from pathlib import Path
import email_notifier as en
from email_notifier import EmailNotifier
import sighting_util as su
import yaml



def load_reporters(path="reporter_config.yaml"):
    reporters = []

    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    reporters_cfg = cfg.get("reporters", {})
    selected_names = [name for name, enabled in reporters_cfg.items()  if str(enabled).lower() in ("yes", "true")]
    print(selected_names)
    for loader, name, is_pkg in pkgutil.iter_modules(['reporter']):
        if name == "base_reporter": continue #skip base report which is a virtual class

        if selected_names and name not in selected_names:
            continue  # 只加载指定的 checker

        module = importlib.import_module(f"reporter.{name}")
        for attr in dir(module):
            cls = getattr(module, attr)
            if isinstance(cls, type) and  issubclass(cls, base_reporter.BaseReporter) and cls != base_reporter.BaseReporter and   cls.__module__ == module.__name__  :
                reporters.append(cls())
                print(f"loaded {cls()}")
    return reporters   





def load_checkers(selected_checker_names=None):
    checkers = []
    for loader, name, is_pkg in pkgutil.iter_modules(['checker']):
        if name == "base_checker": continue

        if selected_checker_names and name not in selected_checker_names:
            continue  # 只加载指定的 checker

        module = importlib.import_module(f"checker.{name}")
        for attr in dir(module):
            cls = getattr(module, attr)
            if isinstance(cls, type) and issubclass(cls, base_checker.BaseChecker) and cls != base_checker.BaseChecker:
                checkers.append(cls())
    return checkers

'''
def checkPlatgSightingMatchingBugeco(sighting_id, sets_data, parm_Json):
    
    ingredient = parm_Json.get("data", [])[0].get(show_fields_generateFullFieldName("ingredient"))
    if not ingredient:
        ingredient = "N.A"
    suspect_area = parm_Json.get("data", [])[0].get(show_fields_generateFullFieldName("suspect_area"))
    if not suspect_area:
        suspect_area = "N.A"
    
    
    print('Platform sighitng ID:' + sighting_id + "Ingredient: " + ingredient +"; suspect_area" + suspect_area)

    found_bugeco = False
    found_sighting_cental = False
    for item in sets_data:
        subject = item.get("subject", "").lower()
        tenant = item.get("tenant", "").lower()
        if "bugeco" in subject:
            found_bugeco = True
            item.get("component", "").lower()
            print("found_bugeco: " + item.get("id") + " with component" + item.get("component", ""))

        if "sighting_central" in tenant:
            found_sighting_cental = True
            item.get("component", "").lower()
            print("found_bugeco: " + item.get("id") + " with component" + item.get("component", ""))


    if not found_bugeco:
        print(f"⚠️ WARNING: Cant find  bugEco for  silicon sighting " + sighting_id )
    
    if not  found_sighting_cental:
        print(f"⚠️ WARNING: Cant find sighting central for  silicon sighting " + sighting_id )
    # how to judget the suspect area and bugeco has the same code? 

    #Then to check if sighting_central in the sets or not. 
            
'''

'''
def show_fields_generateFullFieldName(field):
    prefix = "server_platf.bug."
    if field in ("suspect_area", "ingredient","days_open",  "sighting_submitted_date", "root_caused_date", "transferred_date", "regression","days_sighting_submitted",
                 "days_lastupdate", "days_to_root_caused","days_sighting_submitted", "transferred_id", "root_cause_detail"):
        full_key = prefix + field 
    elif field in ("exposure", "forum", "implemented_date"):
        full_key = prefix[len('server_platf.'):] + field 
    else:
        full_key = field   
    return full_key
'''

                

def add_tag(sighting_id, addTag): 
    # Step 1: Get the id info
    headers = {'Content-type': 'application/json'}
    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'?fetch=false&debug=false'
  
    data = {
      "tenant": "server_platf",
      "subject": "bug",
      "fieldValues": [
        {
          "tag": None
        }
      ]
    }
    
    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    if response.status_code == 200:
        resData = response.json()
        tags = resData['data'][0]['tag']
        
        if tags is not None:
            print("Get Tag of sighting " + sighting_id +" ：" + tags)
        else:
            print( sighting_id + " \’s tag is empty") 
    else:
        print("Failed to fetch data")
        exit()

    tags_list = tags.split(',')   if tags else []
    if addTag not in tags_list:
        tags_list.append(addTag)
        updated_tags = ','.join(tags_list)
        data["fieldValues"][0]["tag"] = updated_tags
        print('To update the tag of ' + updated_tags )
        response = requests.put(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers, json=data)
        
        if response.status_code == 200:
            print(response)
        else:
            print(response)
            print("Failed to update data")
            exit()

def  list_tag(sighting_id, listTag): 
    # Step 1: Get the id info
    headers = {'Content-type': 'application/json'}
    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'?fetch=false&debug=false'
#    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    if response.status_code == 200:
        resData = response.json()
        tags = resData['data'][0]['tag']
        print("Get Tag of sighting " + sighting_id +" ：" + tags)
    else:
        print("Failed to fetch data")
        exit()
    tag_list = tags.split(',')
    for tag in tag_list:
        print(tag)
        
def  remove_tag(sighting_id, removeTag):
    # Step 1: Get the id info
    headers = {'Content-type': 'application/json'}
    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'?fetch=false&debug=false'
    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    if response.status_code == 200:
        resData = response.json()
        tags = resData['data'][0]['tag']
        print("Get Tag of sighting " + sighting_id +" ：" + tags)
    else:
        print("Failed to fetch data")
        exit()
    tags_list = tags.split(',') if tags else []
    if removeTag in tags_list:
        tags_list.remove(removeTag)
        print(f"{removeTag} has been removed from the list.")
    else:
        print("No this tag")
    updated_tags = ','.join(tags_list)
    data = {
      "tenant": "server_platf",
      "subject": "bug",
      "fieldValues": [
        {
          "tag": None
        }
      ]
    }
    data["fieldValues"][0]["tag"] = updated_tags
    print('To update the tag of ' + updated_tags )
    response = requests.put(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers, json=data)
    
    if response.status_code == 200:
        print(data)
    else:
        print("Failed to update data")
        exit()

def updateSuspectAreaIngredient(sighting_id, args):
    # Step 1: Get the id info
    headers = {'Content-type': 'application/json'}
    url = f'https://hsdes-api.intel.com/rest/article/{sighting_id}?fetch=false&debug=false'
    data = {
        "tenant": "server_platf",
        "subject": "bug",
        "fieldValues": []
    }
    if args.updateSuspectArea:
        print(f"suspect area = {args.updateSuspectArea}")
        data["fieldValues"].append({
            "server_platf.bug.suspect_area": args.updateSuspectArea
        })
    print(args.updateIngredient)
    if args.updateIngredient: 
        print(f"Ingredient  = {args.updateIngredient}")
        data["fieldValues"].append({
            "server_platf.bug.ingredient": args.updateIngredient
        })

    if not  args.updateSuspectArea and not args.updateIngredient:
        print(f"Nonthing to update for sighting {sighting_id}")
        return 
    
    print(data)
    response = requests.put(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers, json=data) 
    if response.status_code == 200:
        print(f"Sighting {sighting_id}  updated: {args.updateSuspectArea} and {args.updateIngredient}")
    else:
        print("Failed to update data")
        return
    

def updateField_Parse_with_Excel(sighting_id, field_list):
    update_dict = {
        "tenant": "server_platf",
        "subject": "bug",
        "fieldValues": [

        ]
    }

    blocked_keys = {"suspect_area", "ingredient"}

    if field_list:
        for item in field_list:
            if '=' in item:
                key, value = item.split('=', 1)
                key = key.strip()
                value = value.strip()

                if key in blocked_keys:
                    print(f"❌ Field '{key}' cannot be updated using --updateField.")
                else:
                    update_dict["fieldValues"].append({key: value})
            elif  item in  ["server_platf.bug.executive_summary", 
                            "server_platf.bug.sysdbg_notes1",
                            "server_platf.bug.sysdbg_notes2",
                            "server_platf.bug.sysdbg_notes3",
                            "server_platf.bug.sysdbg_notes4" ] :
                    value_from_excel = su.sighting_read_out_from_working_book(sighting_id, item)
                    if value_from_excel:
                        update_dict["fieldValues"].append({item: value_from_excel})
                    else:
                        print(f"⚠️ not get the content from excel for {item}, skipped.")
            else: 
                print(f"⚠️ skipped argument: {item}")
    else:
        print(f"⚠️ No Field to update")
    # json_body = json.dumps(update_dict)
    return   update_dict





def updateField_Parse_with_txt_file(field_list):
    update_dict = {
        "tenant": "server_platf",
        "subject": "bug",
        "fieldValues": [

        ]
    }

    blocked_keys = {"suspect_area", "ingredient"}

    if field_list:
        for item in field_list:
            if '=' in item:
                key, value = item.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key in blocked_keys:
                    print(f"❌ Field '{key}' cannot be updated using --updateField.")
                else:
                    update_dict["fieldValues"].append({ key : value})
            elif  item in  ["server_platf.bug.executive_summary", 
                            "server_platf.bug.sysdbg_notes1",
                            "server_platf.bug.sysdbg_notes2",
                            "server_platf.bug.sysdbg_notes3",
                            "server_platf.bug.sysdbg_notes4" ] :
                file_path = "paragraph_upload.txt"
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        value = f.read().strip()
                    update_dict["fieldValues"].append({item: value})
                    print(f"✅ Loaded suspect_area from {file_path}")
                except FileNotFoundError:
                    print(f"❌ File not found: {file_path}")
                except Exception as e:
                    print(f"❌ Error reading {file_path}: {e}")

            else: 
                print(f"⚠️ skipped argument: {item}")
    else:
        print(f"⚠️ No Field to update")
    # json_body = json.dumps(update_dict)
    return   update_dict
        
def updateField(sighting_id,  args ):
    # Step 1: Get the id info
    headers = {
        'Content-type': 'application/json',
         'Accept' :  'application/json'    
     }
    
    url = f'https://hsdes-api.intel.com/rest/article/{sighting_id}?fetch=false&debug=false'

    data = updateField_Parse_with_Excel(sighting_id, args.updateField)
    print(data)
    response = requests.put(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers, json=data) 
    if response.status_code == 200:
        if args.updateField:
            print(f'Sighting {sighting_id}  updated: {data["fieldValues"]}')
    else:
        print(response)
        print("Failed to update data")
        return
 

def create_sighting_list(id_list, queryId ):

    id_list_from_query = []
    if queryId:
        o_hsdconn = HSDConnection(queryId)
        o_hsdconn.fetch_data(query_id=queryId)
        id_list_from_query = o_hsdconn.get_query_id_list(queryId)

    return  (id_list or []) + (id_list_from_query )




def check_rule_load_config(path="rule_check_config.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config["subsystems"]

def get_current_week_number():
    # 取当前日期，计算“公司周”，这里假设周日为周起始，使用isocalendar周数再调正
    today = datetime.date.today()
    # 简单用isocalendar周数，示范用，实际可按公司规则修正
    return today.isocalendar()[1]

def main():
    parser = argparse.ArgumentParser(description="HSD Sighting Operations")
    parser.add_argument("--id", nargs="+",  help="Sighting ID")
    parser.add_argument("--queryId", required=False,  help="query  ID") # only accept just 1 query ID
    
    parser.add_argument("--addTag", help="Tag to add")
    parser.add_argument("--removeTag",metavar="TAG",  help="Tag to remove")
    parser.add_argument("--listTag", action='store_true', help="List the tags of the id")
    parser.add_argument("--showField", "--sf", metavar="field" , nargs='+', help="show the sighting's field: suspect_area, ingredient, status, status_reason, forum")
    parser.add_argument("--showLinks", action='store_true', help="show the sighting's links and sets")

    
    #update the ingredient will make more sense. 
    list_suspect_area = [
                        "silicon", "system_boards", "hardware.component.dram",
                        "io_device", "bios","bmc_fw","cpld_fw", 
                        "pfr", "operating_system",  "platform.simics", "DDR5 DIMM", 
                        "documentation", "script", "tool", "test_content", "unknown"

                                # 你可以继续加更多
                        ]
    parser.add_argument("--updateSuspectArea", choices=list_suspect_area, metavar="update suspect_area", help='Choose one of predefined areas: ' + ', '.join(list_suspect_area) )
    parser.add_argument("--updateIngredient", help='Choose one of predefined areas')
    parser.add_argument("--updateField", "--uf",nargs="*" , help='Choose one of predefined areas')
    parser.add_argument("--checkRule", "--cr", metavar="rule",   nargs="*" ,  help='to run the checkers, default is to check owner, all--all rules; the rules are in checker folder')
    parser.add_argument("--sendemail", "--se", action="store_true", help="If specified, send the email. Default is False.")
    
    # for wiki
    parser.add_argument("--toWiki", "--tw",  nargs="?", const=True, help="Put the comment id to wiki paage https://wiki.ith.intel.com/display/oksdebug/Informative+comments")
    parser.add_argument("--pageId", help="Wiki page ID")
    parser.add_argument("--knowledge", help="knowledge type: [pythonsv, link]")

    for domain, cols in su.WIKI_KNOWLEDGE_TYPE_TABLE_CONFIG.items():
        for col in cols.keys():
            parser.add_argument(f"--{col}", help=f"{col} for knowledge of {domain}")


    #for report
    parser.add_argument("--report", "--rt", action="store_true",  help=" report the sighting summarzed info")
    parser.add_argument("--week", "--wk", type=int, nargs="?", default=None, help="week number for report") 
    
    # 其他参数可以在这里添加
    # parser.add_argument("--updateRelease", help="Release to update")
    # parser.add_argument("--updateReleaseAffected", help="Release affected to update")
    # parser.add_argument("--exposure", help="Exposure level to update")
    args  = parser.parse_args()



    import sys
    import io
    import os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

    '''
    command validity dependency:
    id	queryId	addTag	listTag	removeTag	showField	showLinks	updateSuspectArea	
                    id	     id	        id	        id	        id	            id	                
    
    updateIngredient	updateField	 checkrule	                        sendEmail	towiki     report
    id	         id	           id    queryId,id(both null, then yaml)   checkrule	    id     queryId
    '''

    print('start')

    
    if args.report:
        if(not args.queryId):
            print(f"⚠️ WARNING: query id for report" )
            exit()

        sighting_list = create_sighting_list([], args.queryId )
        
        if(args.week):
            week = args.week if args.week else get_current_week_number()    
        else:
            week = 36

        reporters_to_run = load_reporters()
        

        if(args.sendemail):
            o_en = EmailNotifier(f"platform sysdebug report")

        for reporter in reporters_to_run:
            tables = reporter.generate(sighting_list, week)
            if args.sendemail:
                o_en.put_description_to_email(reporter.get_description())
                if isinstance(tables, dict):
                    for name, table_data in tables.items():
                        o_en.add_table(table_data, name)
                else:
                    print(f"Debug -- Table gerated wronngly")

        if(args.sendemail):
            o_en.display()


    if args.checkRule != None:        
        if args.id or  args.queryId :
            sighting_list = create_sighting_list(args.id, args.queryId )
            if not sighting_list: 
                print(f"⚠️ WARNING: No valid sighting id can be found" )
                exit()

            requested_rules = args.checkRule
            if requested_rules == []:
                print(f"⚠️ WARNING: need to assign rules to check, or use 'all' " )
                exit()
            elif "all" in requested_rules :
                rule_checkers  = load_checkers()
            else:
                rule_checkers = load_checkers(requested_rules)
            su.sighting_check_sightings_based_on_rules(sighting_list, rule_checkers, args.sendemail)

        else:
            print(f"no id or queryid, so load from yaml config file")
            subsystem_list = check_rule_load_config()

            if not subsystem_list :
                print(f"⚠️ WARNING: cant get valid config.yaml file" )
                exit()

            for subsystem in subsystem_list:
                query_id = subsystem["query_id"]
                name = subsystem.get("name", "Unknown")
                send_email = subsystem.get("send_email", "no") == "yes"

             
                rules = subsystem.get("rules", "all")
                if rules == "all":
                    # 加载所有规则脚本（如：遍历 checker 文件夹）
                    rule_checkers = load_checkers()
                else:
                    # 只加载指定规则名的脚本
                    rule_checkers = load_checkers(rules)

               #for this sub system to get the sighting list (from query id ) rules.                
                sighting_list = create_sighting_list([], query_id )

                print(f"\n🔍 Running rules for {name} (query_id: {query_id}, rules:{rule_checkers})")     

                #start running for 1 sub system.
                su.sighting_check_sightings_based_on_rules(sighting_list,rule_checkers, name, args.sendemail  )

    def handle_wiki_command_arg(command_arg) : 
        """支持传 txt 文件路径"""
        if command_arg and os.path.isfile(command_arg) :
            with open(command_arg, "r", encoding="utf-8") as f:
                return f.read()
        print(f"read file done!")
        return command_arg or ""

    if args.toWiki:
        if  args.pageId is None and args.knowledge is None:
            su.wiki_add_comment_id_to_page(args.toWiki)
        elif args.knowledge or (args.pageId and  args.knowledge):
                # 动态添加 domain 对应列的参数
            row_data = {}
            for col in su.WIKI_KNOWLEDGE_TYPE_TABLE_CONFIG[args.knowledge].keys():
                value = getattr(args, col)
                if col == "command":  # 特殊处理
                    value = handle_wiki_command_arg(value)
                row_data[col] = value or ""
            if args.pageId : 
                pageId = args.pageId
            else:
                pageId = su.WIKI_DEFAULT_PAGE_IDS[args.knowledge] 
            su.wiki_add_row_to_page(pageId, args.knowledge , row_data)


    if args.addTag or args.listTag or args.removeTag :
        if not len(args.id) :
             print("❌ Please provide at least one one ")
             sys.exit(1)


    if args.addTag:
        print('To run the function of addTag')
        for sighting_id in  args.id:
            add_tag(sighting_id, args.addTag)
    
    if args.listTag:
        print('To list the tag')
        for sighting_id in  args.id:
            list_tag(sighting_id, args.listTag)
        
    if args.removeTag:
        print('To remove tag'+ ' ' + args.removeTag)
        for sighting_id in  args.id:
            remove_tag(sighting_id, args.removeTag)

    if args.showField:
        print("To show the fields")
        for sighting_id in  args.id:
            su.sighting_show_field(sighting_id, args.showField)
            
    if args.showLinks:
        if not len(args.id):
            print("❌ Please provide at least one --id.Empty values are not allowed. Can't perfrom: " + "show links" )
        else:
            print("To show the links")
            for sighting_id in args.id:
                su.sighting_show_links_sets(sighting_id)

    if args.updateSuspectArea or args.updateIngredient:
        if not len(args.id):
            print("❌ Please provide at least one ID --id.Empty values are not allowed. Can't perfrom: " + "update suspect area" )    
        else: 
            print("To update the suspect area\n")
            for sighting_id in args.id :
                updateSuspectAreaIngredient(sighting_id,  args )

    if args.updateField:
        if not len(args.id):
            print("❌ Please provide at least one ID --id.Empty values are not allowed. Can't perfrom: " + "update suspect area" )    
        else:
            print("To update the fileds\n")
            for sighting_id in  args.id:
                updateField(sighting_id,  args )

    # 其他参数的处理逻辑可以在这里添加
    # if args.updateRelease:
    #     update_release(sighting_id, args.updateRelease)
    # if args.updateReleaseAffected:
    #     update_release_affected(sighting_id, args.updateReleaseAffected)
    # if args.exposure:
    #     update_exposure(sighting_id, args.exposure)

 
if __name__ == "__main__":
    main()


    

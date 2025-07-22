import requests
from requests_kerberos import HTTPKerberosAuth
import json
import pandas as pd
import argparse
import checkLinks as cL


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


def checkSighitngsWithQuery(query_id, type="silicon"):
    #using query to get the list
    #for each sighing in the list, get the sets
    #if ingredient is null or not containing the silicon, reporting warning
    #if ingredient contains' silicon, if set is null or doesn't have bugEco , reporting warining
    #    continue check: -- It it has transferred ID, check if transferred ID, reporting need to check the transferred id.
    #if ingredient contain "pcode", 'oCode", the bugEco component should have those. 
    headers = {'Content-type': 'application/json'}
    url = 'https://hsdes-api.intel.com/rest/query/' + query_id +'?include_text_fields=Y&start_at=1&max_results=10000&fields=id%2Ctitle'
    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)

    if response.status_code == 200:
        data = response.json()
        id_list = [item['id'] for item in data['data']]
    else:
        print("Failed to fetch data")
        exit()
    print(id_list)
    

    expected_fields_in_sets = [
    'id', 'subject', 'tenant', 'title', 'status',
    'owner', 'from_id', 'from_tenant', 'component', 'component_affected'
    ]

    fields_url_in_sets= ','.join(expected_fields_in_sets)
    #expected_fields_in_sets = 'fields= id%2Csubject%2Ctenant%2Ctitle%2Cstatus%2Cowner%2Cfrom_id%2Cfrom_tenant%2Ccomponent%2Ccomponent_affected'
   
    for sighting_id in id_list:
        try:
            sets_url = f'https://hsdes-api.intel.com/rest/article/{sighting_id}/sets?fields={fields_url_in_sets}'
            parm_url = f'https://hsdes-api.intel.com/rest/article/{sighting_id}?fetch=false&debug=false'

            sets_res =  requests.get(sets_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
            if sets_res.status_code == 200:
                sets_Json = sets_res.json()
                #print(linksData)
            else: 
                print(sets_Json)
                print("Can't retrieve Sets data of " + sighting_id +" continue next one")
                continue

            parm_res = requests.get(parm_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)           
            if parm_res.status_code == 200:
                    parm_Json = parm_res.json()
            else:
                print(parm_Json)
                print("can't retrieve sighitng" + sighting_id + " data, continue next one")
                continue
        except requests.RequestException as e:
            print(f"\n❌ 网络请求错误 for ID {sighting_id}: {e}")
            continue  # 跳过当前这个 ID，继续下一个
        except ValueError as e:
            print(f"\n❌ JSON 解码失败 for ID {sighting_id}: {e}")
            continue

        ingredient = parm_Json.get("data", [])[0].get(show_fields_generateFullFieldName("ingredient"))  
        if not ingredient:
            ingredient = "N.A"
        suspect_area =  parm_Json.get("data", [])[0].get(show_fields_generateFullFieldName("suspect_area"))  
        if not suspect_area: 
            suspect_area = "N.A"

        title = parm_Json.get("data", [])[0].get(show_fields_generateFullFieldName("title"))  
        sets_data = sets_Json.get("data", [])
        
        if ("silicon" not in str(ingredient).lower()) and ("silicon" not in str(suspect_area).lower()):
            print(f"⚠️ Info: Neither ingredient nor suspect_area contains 'silicon' {sighting_id}: {title}")
            print(f"⚠️ Info: ingredient:{ingredient}  suspect_area:{suspect_area}")

   
            #then check if any bugeco in the non-silicon sighting.
            
            found_bugeco = False

            for item in sets_data:
                subject = item.get("subject", "").lower()
                #from_tenant = item.get("from_tenant", "").lower()

                if "bugeco" in subject :
                    print(f"⚠️ WARNING: Found bugEco in subject  for non_silicon ID" + sighting_id + " ---->" + item.get('id'))
                    found_bugeco = True
                    break  # 如果你只想要找到一个就够了，可以加这个
            print()
            '''
            if not found_bugeco:
                print("✅ No bugEco found in sets.")
            '''
        else:
          #then check if any bugeco in the non-silicon sighting.
           checkPlatgSightingMatchingBugeco(sighting_id,  sets_data, parm_Json )

            


def show_fields_generateReqURL():
    print('hello world')

def show_fields_generateReqURLAndData():
    print('hello world')

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

def showField(sighting_id, user_fields): 
   # Step 1: Get the id info
    headers = {'Content-type': 'application/json'}
    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'?fetch=false&debug=false'
#    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    response = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    if response.status_code == 200:
        resData = response.json()
        #tags = resData['data'][0]['tag']
    else:
        print("Failed to fetch data")
        exit()

    for entry in resData.get("data", []):
        for field in user_fields:
            full_key = show_fields_generateFullFieldName(field)
            value =  entry.get(full_key)
            if not value:
                value = "N.A"
            print(f'sighting {sighting_id} field {field}: ' + value)

                

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
    

def updateField_Parse(field_list):
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
            else:
                print(f"⚠️ Invalid format (should be key=value): {item}")
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

    data = updateField_Parse(args.updateField)
    print(data)
    response = requests.put(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers, json=data) 
    if response.status_code == 200:
        if args.updateField:
            print(f'Sighting {sighting_id}  updated: {data["fieldValues"]}')
    else:
        print(response)
        print("Failed to update data")
        return
 




def main():
    parser = argparse.ArgumentParser(description="HSD Sighting Operations")
    parser.add_argument("--id", nargs="+",  help="Sighting ID")
    parser.add_argument("--addTag", help="Tag to add")
    parser.add_argument("--removeTag", help="Tag to remove")
    parser.add_argument("--listTag", action='store_true', help="List the tags of the id")
    parser.add_argument("--showField", nargs='+', help="show the sighting's field: suspect_area, ingredient, status, status_reason, forum")
    parser.add_argument("--showLinks", action='store_true', help="show the sighting's links and sets")
    parser.add_argument("--traceByQueryId", nargs='+',help='check the sanity of a given query for the suspect_area/Ingredient')
    
    #update the ingredient will make more sense. 
    list_suspect_area = [
    "silicon", "system_boards", "hardware.component.dram","io_device", "bios","bmc_fw","cpld_fw", "pfr"
    "operating_system",  "platform.simics", "DDR5 DIMM", "documentation", "script", "tool", "test_content"

    # 你可以继续加更多
    ]
    parser.add_argument("--updateSuspectArea", choices=list_suspect_area, help='Choose one of predefined areas')
    parser.add_argument("--updateIngredient", help='Choose one of predefined areas')
    parser.add_argument("--updateField",nargs="*" , help='Choose one of predefined areas')
    
    # 其他参数可以在这里添加
    # parser.add_argument("--updateRelease", help="Release to update")
    # parser.add_argument("--updateReleaseAffected", help="Release affected to update")
    # parser.add_argument("--exposure", help="Exposure level to update")

    args = parser.parse_args()

    if (not args.id and not args.traceByQueryId ):
        exit()

    print('start')
    if args.addTag or args.listTag or args.removeTag :
        if not len(args.id) or len(args.id) > 1:
             print("❌ Please provide exactly one --id. Multiple or empty values are not allowed.")
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
            showField(sighting_id, args.showField)
            
    if args.showLinks:
        if not len(args.id):
            print("❌ Please provide at least one --id.Empty values are not allowed. Can't perfrom: " + "show links" )
        else:
            print("To show the links")
            for sighting_id in args.id:
                cL.ShowWworkflow(sighting_id)
    
    if args.traceByQueryId:
        if not len(args.traceByQueryId) or  len(args.traceByQueryId) > 1:
            print("❌ Please provide exactly one --id. Multi and Empty values are not allowed. Can't perfrom: " + "Check Sightings with Query" )
        else:
            print("To show the links")
            queryId =  args.traceByQueryId[0]
            checkSighitngsWithQuery(queryId)
   
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


    

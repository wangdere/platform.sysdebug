import requests
from  hsd_connection  import HSDConnection
import hsd_types as ht 
from requests_kerberos import HTTPKerberosAuth
from requests.auth import HTTPBasicAuth
import urllib3
def sighting_get_debug_stage(o_hsd_conn):

    sighting_status = o_hsd_conn.get_sighting_field_value(ht.SightingFieldEnum.status)
    sighting_status_reason = o_hsd_conn.get_sighting_field_value(ht.SightingFieldEnum.status_reason)

    if sighting_status == ht.PlatfStatus.open:
        print(sighting_status)
        if sighting_status_reason == ht.PlatfStatusReason.assigned or \
            sighting_status_reason == ht.PlatfStatusReason.awaiting_3rd_party or \
            sighting_status_reason == ht.PlatfStatusReason.awaiting_customer or \
            sighting_status_reason == ht.PlatfStatusReason.awaiting_development or \
            sighting_status_reason == ht.PlatfStatusReason.awaiting_submitter or \
            sighting_status_reason == ht.PlatfStatusReason.clone or \
            sighting_status_reason == ht.PlatfStatusReason.code_review or \
            sighting_status_reason == ht.PlatfStatusReason.development or \
            sighting_status_reason == ht.PlatfStatusReason.new or \
            sighting_status_reason == ht.PlatfStatusReason.promoted or \
            sighting_status_reason == ht.PlatfStatusReason.re_open or \
            sighting_status_reason == ht.PlatfStatusReason.verify_failed:
            return ht.DebugStage.Assigned
        elif  sighting_status_reason == ht.PlatfStatusReason.transferred:
            return ht.DebugStage.Transferred
        elif sighting_status_reason == ht.PlatfStatusReason.root_caused:
            return ht.DebugStage.Root_Caused
        else:
            return ht.DebugStage.Assigned
    elif sighting_status == ht.PlatfStatus.implemented:
        if sighting_status_reason == ht.PlatfStatusReason.await_user_verify:
            return ht.DebugStage.Impl_AwaitingVerify
        else:
            return ht.DebugStage.Impl_AwaitIngredientRelease
    elif sighting_status == ht.PlatfStatus.verified:
            return ht.DebugStage.Verified
    elif sighting_status == ht.PlatfStatus.rejected:
            return ht.DebugStage.Rejected
    else:
            return ht.DebugStage.Closed


def is_a_silicon_sighting(o_hsd_conn):
    ingredient=  o_hsd_conn.get_sighting_field_value("ingredient") or ""
    suspect_area= o_hsd_conn.get_sighting_field_value("suspect_area") or  ""
    if sighting_get_debug_stage(o_hsd_conn) in [ ht.DebugStage.Assigned ,ht.DebugStage.Rejected ] :
        return False

    else:
        if "silicon" in suspect_area or "silicon" in ingredient :
             return True
        else:
             return False
        

def is_a_bios_sighting(o_hsd_conn):
    if sighting_get_debug_stage(o_hsd_conn) in [ ht.DebugStage.Assigned ,ht.DebugStage.Rejected ] :
        return False
    else:
        ingredient=  o_hsd_conn.get_sighting_field_value("ingredient") or ""
        suspect_area= o_hsd_conn.get_sighting_field_value("suspect_area")  or ""
        if "bios" in suspect_area or "bios" in ingredient:
            return True
        else:
            return False

def is_silicon_solution_in_sets(o_hsd_conn):
    sets_data = o_hsd_conn.get_sighting_sets_json()
    result = False
    for item in sets_data['data']:
        sets_item_id = item.get("id", "").lower()
        subject = item.get("subject", "").lower()
        tenant = item.get("tenant", "").lower()
        set_item_status = item.get("status", "").lower()
        from_tenant = item.get("from_tenant", "") or ""
        component = item.get("component", "") or ""

        if "sighting_central" in from_tenant:
            if sets_item_id == o_hsd_conn.sighting_id : # this is the sighting itself
                return False

        else:
            if ( set_item_status != "rejected"):
                if "bugeco" in subject :
                    result = True
                non_silicon_key_words = ["tool", "sw", "doc", "val."]
                if "sighting_central" in tenant and all(kw not in component for kw in non_silicon_key_words):
                    result= True

    return result

def is_bios_solution_in_sets(o_hsd_conn):
    sets_data = o_hsd_conn.get_sighting_sets_json()
    result = False
    for item in sets_data['data']:
        subject = item.get("subject", "").lower()
        tenant = item.get("tenant", "").lower()
        set_item_status = item.get("status", "").lower()
        from_tenant = item.get("from_tenant", "") or ""
        component = item.get("component", "") or ""

        if "bios" in from_tenant:
            return False

        else:
            if ( set_item_status != "rejected"):
                if "central_firmware" in tenant :
                    result= True
    return result


def sighting_show_field(sighting_id, user_fields): 
    o_hsdconn = HSDConnection(sighting_id)
    o_hsdconn.fetch_data(sighting_id=sighting_id,sighting_field_list=user_fields )

    resData = o_hsdconn.get_sighting_json(sighting_id)
    # 合并所有字典
    merged = {}
    for d in resData['data']:
        merged.update(d)
    # 打印每个 key 和 value
    for k, v in merged.items():
        print(f"{k}: {v}")


def wiki_get_page_data(page_id = "4260912289"):
    # 关闭自签名证书告警（Intel 内网常见）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = "https://wiki.ith.intel.com/rest/api/content/4260912289?expand=version"

    # 用 curl 中 -u 的账号密码
    auth = HTTPBasicAuth("wangdere", "aa.bb.1122")

    headers = {
        "Authorization": "Bearer MDQyODA5Mzk4Njc3OnCzEOxvVO4r1PktqW9qj4Cur9KW"
    }

    response = requests.get(url, auth=auth, verify=False)

    print("Status code:", response.status_code)
    print("Response:")
    print(response.text)
    return response.json()

def wiki_add_comment_id_to_page(parent_id, comment_id, page_id = "4260912289"):

        
    # 关闭自签名证书告警（Intel 内网常见）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    
    url_put = "https://wiki.ith.intel.com/rest/api/content/4260912289"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer MDQyODA5Mzk4Njc3OnCzEOxvVO4r1PktqW9qj4Cur9KW"
    }

    current_page_data = wiki_get_page_data()
    old_version = current_page_data['version']['number']
    old_title = current_page_data['title']
    old_type = current_page_data['type']    
    data = { 
        "title": old_title,
        "type": old_type,
        "version":{
            "number": old_version + 1
        }  ,
        "body": {
            "storage": {
                "value": f"<p>Hello <strong>World</strong> from Python !. Add Parent ID = {parent_id}, comment_id = {comment_id}</p>",
                "representation": "storage"
            }
        }
    }
    

    response = requests.put(url_put, json=data,  headers=headers, verify=False)
    print("Status code:", response.status_code)
    print(response.text)

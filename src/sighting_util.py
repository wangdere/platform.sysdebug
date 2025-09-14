import requests
from  hsd_connection  import HSDConnection
import hsd_types as ht 
from requests_kerberos import HTTPKerberosAuth
from requests.auth import HTTPBasicAuth
import urllib3
from bs4 import BeautifulSoup
from email_notifier import EmailNotifier
from tabulate import tabulate
import shutil
from datetime import datetime
import re
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
        set_item_status_reason = item.get("status_reason", "").lower()
        from_tenant = item.get("from_tenant", "") or ""
        component = item.get("component", "") or ""
        '''
        if "sighting_central" in from_tenant:
            
            if set_item_status == "rejected" and set_item_status_reason == "merged": 
                result =  True   # here will not trace more deeper into merged sighting. 
            else:
                non_silicon_key_words = ["tool", "sw", "doc", "val.", "board",  "dimm"]
                if ( component !=""):
                    if "sighting_central" in tenant and all(kw not in component for kw in non_silicon_key_words):
                        result = True
                else:
                    result = False
        else:
            if "bugeco" in subject:
                result = True
                if set_item_status == "rejected" and set_item_status_reason != "merged": 
                    result =  False
        '''
        if "sighting_central" == tenant:
            if set_item_status == "rejected": 
                if set_item_status_reason == "merged" : 
                    result = True
            else: 
                non_silicon_key_words = ["tool", "sw", "doc", "val.", "board",  "dimm"]
                if ( component !=""):
                    if all(kw not in component for kw in non_silicon_key_words):
                        result = True
        else:
            if "bugeco" in subject:
                result = True
                if set_item_status == "rejected" and set_item_status_reason != "merged": 
                    result =  False

        if result == True : # already found
            break

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


def sighting_check_sightings_based_on_rules(sighting_list, rule_list, name="PV", sendemail = True):
    
            #start running for 1 sub system.
        if(sendemail):
            o_en = EmailNotifier(f"platform sysdebug check summary--{name}")
        for checker in rule_list:
            if(sendemail):
                o_en.put_description_to_email(checker.rule_name)
                o_en.add_result_table_header()
            for sighting_id in  sighting_list:
                o_hsdconn = HSDConnection(sighting_id)
                o_hsdconn.fetch_data(sighting_id=sighting_id )
                
                passed, msg = checker.run(o_hsdconn)
                status = "✅" if passed else "⚠️"
                if(sendemail):
                    o_en.add_rule_result(o_hsdconn, passed, msg)
                print(f"{status} {msg}")
            if(sendemail):
                o_en.put_table_to_email()
        if(sendemail):
            o_en.put_footer()
            o_en.display()


def wiki_get_page_data(page_id = "4260912289"):
    # 关闭自签名证书告警（Intel 内网常见）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = f"https://wiki.ith.intel.com/rest/api/content/{page_id}?expand=body.storage,version.number"

    # 用 curl 中 -u 的账号密码
    auth = HTTPBasicAuth("wangdere", "aa.bb.1122")

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer MDQyODA5Mzk4Njc3OnCzEOxvVO4r1PktqW9qj4Cur9KW"
    }

    response = requests.get(url, headers=headers, verify=False)
    if(response.status_code == 200): 
        print("Get Wiki page data, Status code:", response.status_code)
        # print("Response:")
        # print(response.text)
        return response.json()
    else:
        print(f"cant  get page data of {url}")
        return None


def wiki_add_comment_id_to_page(comment_id, page_id = "4260912289"):


    # 关闭自签名证书告警（Intel 内网常见）
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    current_page_data = wiki_get_page_data()
    if  not current_page_data: 
            return 
    else:
        old_html = current_page_data["body"]["storage"]["value"]
        old_version = current_page_data['version']['number']
        old_title = current_page_data['title']
        old_type = current_page_data['type']    

        soup = BeautifulSoup(old_html, "html.parser")

        table = soup.find("table", {"class": "comment_list_table"})

        if table == None:
                # 没找到目标表，就新建
            table = soup.new_tag("table", attrs={"class": "comment_list_table"})
            header = soup.new_tag("tr")
            for col in ["comment_id", "updated_date", "submitted_by", "title"]:
                th = soup.new_tag("th")
                th.string = col
                header.append(th)
            table.append(header)
            
            # 插入到页面末尾，也可以选择插入到某个特定div
            soup.append(table)
        
        # 找到 header 的列顺序，确定 comment_id 是第几列
        header_row = table.find("tr")
        headers = [th.text.strip() for th in header_row.find_all("th")]

        try:
            comment_id_index = headers.index("comment_id")
        except ValueError:
            raise Exception("❌ 表头中找不到 'comment_id'")

        # 遍历所有数据行，提取 comment_id 列的数据
        existing_comment_ids = []
        for row in table.find_all("tr")[1:]:  # 跳过 header 行
            cols = row.find_all("td")
            if len(cols) > comment_id_index:
                value = cols[comment_id_index].text.strip()
                existing_comment_ids.append(value)

        # 检查是否存在
        if comment_id in existing_comment_ids:
            return



        # found the table, at least it has a header
        o_comment_conn = HSDConnection(sighting_id=comment_id)
        o_comment_conn.fetch_data(sighting_id=comment_id)


        comment_id = o_comment_conn.comment_get_value_by_field("id")
        updated_date = o_comment_conn.comment_get_value_by_field("updated_date")
        submitted_by = o_comment_conn.comment_get_value_by_field("submitted_by")
        description = o_comment_conn.comment_get_value_by_field("description")
        briefing = description

        comment_s_parent_id = o_comment_conn.comment_get_value_by_field("parent_id")
        o_conn =  HSDConnection(comment_s_parent_id)
        o_conn.fetch_data(sighting_id =  comment_s_parent_id)

        parent_title = o_conn.comment_get_value_by_field("title")

        new_row_data =  f"""
            <tr>
                <td><a href="https://hsdes.intel.com/appstore/article-one/#/article/{comment_id}">{comment_id}</a></td>
                <td>{updated_date}</td>
                <td>{submitted_by}</td>
                <td>{parent_title}</td>
            </tr>
            """

        new_row_soup = BeautifulSoup(new_row_data, "html.parser")
        new_tr= new_row_soup.find("tr")
        tbody = table.find("tbody")
        tbody.append(new_tr)
        new_html = str(soup)



        status, resp_text = wiki_update_page_html(new_html, old_version +1,page_id,old_title, old_type )
        print(f"Wiki Update Status: {status}")



def wiki_update_page_html(new_html, version,page_id,  page_title, page_type):

    #url = f"{WIKI_BASE_URL}/rest/api/content/{page_id}"
    url_put = f"https://wiki.ith.intel.com/rest/api/content/{page_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer MDQyODA5Mzk4Njc3OnCzEOxvVO4r1PktqW9qj4Cur9KW"
    }
    
    data = { 
        "title": page_title,
        "type": page_type,
        "version":{
            "number": version
        }  ,
        "body": {
            "storage": {
                "value": new_html,
                "representation": "storage"
            }
        }
    }
        
    print(f"To update the wiki page with: {page_title}")
    response = requests.put(url_put, json=data,  headers=headers, verify=False)
    print("Status code:", response.status_code)
    #print(response.text)
    return response.status_code, response.text



# === 截断函数
def sighting_helper_func_shorten(text, max_len, from_tail=False):
    if text is None:
        return ""
    text = str(text)

    if from_tail:
        return '...' + text[-(max_len - 3):] if len(text) > max_len else text
    else:

        return text if len(text) <= max_len else text[:max_len - 3] + '...'

def sighting_show_links_sets(sighting_id):
    #print("Hello World")
    #Get the link list of the sighting
    # Step 1: Get the id info
    headers = {'Content-type': 'application/json'}
    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'?fields=id%2Ctitle%2Ctenant%2Csubject%2Cstatus%2Csubject%2Cserver_platf.bug.ingredient%2Cserver_platf.bug.suspect_area'
    sighting = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    sighting_json = sighting.json()
    sighting_data= sighting_json['data'][0]

    self_id = sighting_data['id'] 
    self_tenant = sighting_data['tenant']
    self_subject = sighting_data['subject']
    self_title = sighting_data['title']
    self_status = sighting_data['status']
    self_suspect_area = sighting_data['server_platf.bug.suspect_area'] if sighting_data['tenant'] == "server_platf" else "N.A"
    self_ingredient =  sighting_data['server_platf.bug.ingredient']  if sighting_data['tenant'] == "server_platf" else "N.A"

#    print(sighting_data)
    
    table = []
    tbl_header = ["Type", "ID", "Tenant", "Subject", "Title", "Status"]
    table.append(["Self", self_id, self_tenant, self_subject, self_title[:70], self_status])
    
    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'/links?fields=id%2Ctenant%2Csubject%2Ctitle%2Cowner%2Cstatus%2Clink_type'
    links = requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    if links.status_code == 200:
        linksData = links.json()
        #print(linksData)
    
    for item in linksData['responses']:
        link_type = item.get('link_type')
        tenant = item.get('tenant')
        subject = item.get('subject')
        id_ = item.get('id')
        title = item.get('title')
        status = item.get('status')

        '''
        if link_type == 'clone':
            print(f"[CLONE] id: {id_}, tenant: {tenant}, subject: {subject}, title: {title}, status: {status}")
        elif f"{tenant}.{subject}" != "server_platf.bug":
            print(f"[OTHER] id: {id_}, tenant: {tenant}, subject: {subject}, title: {title}, status: {status}")
        '''
        if link_type == 'clone':
            table.append(["CLONE", id_, tenant, subject, title[:70], status])
        elif f"{tenant}.{subject}" != "server_platf.bug":
            table.append(["OTHER", id_, tenant, subject, title[:70], status])
    #print the important sighting paramter
    print(f"{sighting_id}: suspct_area {str(self_suspect_area) if self_suspect_area is not None else ''}; ingrdient {str(self_ingredient) if self_ingredient is not None else ''}; status {str(self_status) if self_status is not None else ''}")

        # 打印links表格
    print('Check '+ sighting_id+' links' )
    print(tabulate(table, headers=tbl_header, tablefmt="fancy_grid"))
    print('Check '+ sighting_id+'\'s sets' )

    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'/sets?fields=id%2Csubject%2Ctenant%2Ctitle%2Cstatus%2Cowner%2Cfrom_id%2Cfrom_tenant%2Ccomponent'
    sets =  requests.get(url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=headers)
    if sets.status_code == 200:
        setsJson = sets.json()
        #print(linksData)
    else: 
        print(sets)
        print("Can't retrieve Sets data")
    
    ''' direclty print, format will be in a mess
        # 提取字段作为表头
    tbl_headers = setsJson['data'][0].keys()

    # 提取行数据
    rows = [entry.values() for entry in setsJson['data']]

    # 打印表格
    print(tabulate(rows, headers=tbl_headers, tablefmt='grid'))
    '''
    '''
    # === 获取终端宽度
    terminal_width = shutil.get_terminal_size().columns

    # === 设置最大列宽度（平均分配，略去边框宽度）

    if setsJson['data']:
        tbl_headers = list(setsJson['data'][0].keys())
    else:
        print("No sets data available.")
        exit()  # 或者 exit()，根据你的程序结构决定
    
    max_col_width = min(18, terminal_width // len(headers) - 4)
    '''
    tbl_header = ["From_id", "From_tenant", "Id", "Title", "component", "Status","Tenant","Subject"]
    # === 构造缩短内容的表格数据
    rows = []
    for entry in setsJson['data']:
        #row = [shorten(entry.get(h), 50 if h == 'title' else max_col_width) for h in tbl_headers]
         
        row = [entry.get("from_id"),entry.get("from_tenant"),entry.get("id"), sighting_helper_func_shorten(entry.get("title"), 50), 
               sighting_helper_func_shorten( entry.get("component"), 20, True),
               entry.get("status"),entry.get("tenant"),entry.get("subject")]
        rows.append(row)

    # === 打印表格
    print(tabulate(rows, headers=tbl_header, tablefmt='grid'))


def parse_workweek_to_date(re, ww_str: str) -> datetime:
    """
    把 w38 / ww38 / w38.1 / ww38.2 转换成 datetime。
    """
    # 补全格式，比如 w38 → w38.0
    print(f"caputured scrub_notes{ww_str}")
    if re.fullmatch(r"w{1,2}\d{2}", ww_str.lower()):
        ww_str = ww_str + ".0"

    match = re.match(r"w{1,2}(\d{2})\.(\d)", ww_str.lower())
    if not match:
        return None

    week, day = int(match.group(1)), int(match.group(2))

    week = week - 1

    year = datetime.now().year
    weekday = day % 7    # .0 → 周日，.1 → 周一 ... +1 is for intel calendar
    date_str = f"{year} {week} {weekday}"
    return datetime.strptime(date_str, "%Y %W %w")         

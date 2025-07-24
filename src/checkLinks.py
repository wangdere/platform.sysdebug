import requests
from requests_kerberos import HTTPKerberosAuth
import json
import pandas as pd
import argparse
from tabulate import tabulate
import shutil

# === 截断函数
def shorten(text, max_len):
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= max_len else text[:max_len - 3] + '...'

def  ShowWworkflow(sighting_id):
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

    url = 'https://hsdes-api.intel.com/rest/article/'+sighting_id+'/sets?fields=id%2Csubject%2Ctenant%2Ctitle%2Cstatus%2Cowner%2Cfrom_id%2Cfrom_tenant'
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
    tbl_header = ["Owner", "From_id", "From_tenant", "Id", "Title", "Status","Tenant","Subject"]
    # === 构造缩短内容的表格数据
    rows = []
    for entry in setsJson['data']:
        #row = [shorten(entry.get(h), 50 if h == 'title' else max_col_width) for h in tbl_headers]
        row = [entry.get("owner"), entry.get("from_id"),entry.get("from_tenant"),entry.get("id"), shorten(entry.get("title"), 50),entry.get("status"),entry.get("tenant"),entry.get("subject")]
        rows.append(row)

    # === 打印表格
    print(tabulate(rows, headers=tbl_header, tablefmt='grid'))



def main():
    parser = argparse.ArgumentParser(description="Check A Specific Sighting Workflow")

    parser.add_argument("--id", default="15017719069", help="Sighting ID (default: 15017719069)")

    args = parser.parse_args()

    sighting_id = args.id

    ShowWworkflow(sighting_id)

if __name__ == "__main__":
    main()


    


import requests
from requests_kerberos import HTTPKerberosAuth
import urllib3
import json
import shutil
#import PlatfSysdebug as pfsd

class HSDConnection:
    def __init__(self, sighting_id='', query_id = ''):
            self.sighting_id = sighting_id
            self.query_id = query_id
            self.base_url = "https://hsdes-api.intel.com/rest/article/"
            self.sighting_url = None
            self.sighting_link_url = f"{self.base_url}{sighting_id}/links?fields=id%2Ctenant%2Csubject%2Ctitle%2Cowner%2Cstatus%2Clink_type"
            self.sighting_sets_url = f"{self.base_url}{sighting_id}/sets?fields=id%2Csubject%2Ctenant%2Ctitle%2Cstatus%2Cowner%2Cfrom_id%2Cfrom_tenant"
#            self.sighting_links_base_url = f"{self.base_url}{sighting_id}/links?fields=" # to append fields
#            self.sighting_sets_base_url = f"{self.base_url}{sighting_id}/sets?fields=" # to append fields
            self.query_url= f"https://hsdes-api.intel.com/rest/query/execution/{query_id}?include_text_fields=Y&start_at=1&max_results=10000&include_query_fields=Y" # to append fields
            self.headers = {'Content-type': 'application/json'}
            self.sighting_json = None
            self.sighting_link_json = None
            self.sighting_sets_json = None
            self.query_json = None
            self.query_id_list = None
            self.sighting_history_json = None
            # 认证略去

    def get_full_field_name(self, field):
        prefix = "server_platf.bug."
        if field in ("suspect_area", "ingredient","days_open",  "sighting_submitted_date", "root_caused_date", "transferred_date", "regression","days_sighting_submitted",
                    "days_lastupdate", "days_to_root_caused","days_sighting_submitted", "transferred_id", "root_cause_detail", "scrub_notes","ingredient","root_cause_detail"):
            full_key = prefix + field 
        elif field in ("exposure", "forum", "implemented_date"):
            full_key = prefix[len('server_platf.'):] + field 
        else:
            full_key = field   
        return full_key

    def fetch_data(self, *, sighting_id=None, query_id=None, sighting_field_list=None, query_field_list=None, \
                    fetch_links=True, fetch_sets=True, fetch_comments=False, fetch_history = False):
        #if no these two ids, no action
        if not sighting_id and not query_id:
            print(f"❌ Error: Either sighting_id {sighting_id} or queryid {query_id} must be provided.")
            return None
        
        self.sighting_id = sighting_id
        self.query_id = query_id
        
        '''
        if not sighting_id:
            if fetch_links or fetch_sets: 
                 print("✅ Info: Links and Sets can only be got when you assign an sighting_id")
        
        if not query_id: 
             print("✅ Info: Links and Sets can only be fetched for a sighting, not query")
        '''
        #get sighting data
        if sighting_id:
            # Step 1: Get the id info
            self.sighting_url = f"{self.base_url}{sighting_id}?fetch=false&debug=false"
            response = requests.get(self.sighting_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=self.headers)
            if response.status_code == 200:
                res_json = response.json()
                #tags = resData['data'][0]['tag']
            else:
                print(f"Failed to fetch {sighting_id} data with response code {response.status_code} ")
                print(f"request URL: {self.sighting_url}")
                return None
            
            if sighting_field_list:
                #create a empty jason first then append the expected fields to that for a new json strucutrre.
                self.sighting_json= {
                    "data": [
                    ]
                }
                for entry in res_json.get("data", []):
                    for field in sighting_field_list:
                        full_key = self.get_full_field_name(field)
                        value =  entry.get(full_key)
                        if not value:
                            value = "N.A"
                        self.sighting_json['data'].append({full_key: value})
                        # print(f'sighting {sighting_id} field {field}: ' + value)
            else:
                self.sighting_json = res_json

        #get query data
        if query_id:
            if(query_field_list):
                self.query_url = f"https://hsdes-api.intel.com/rest/query/execution/{query_id}?include_text_fields=Y&start_at=1&max_results=100000&fields={','.join(query_field_list)}"
            else:
                self.query_url = f"https://hsdes-api.intel.com/rest/query/execution/{query_id}?include_text_fields=Y&start_at=1&max_results=100000&include_query_fields=Y"

            response = requests.get(self.query_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=self.headers)

            if response.status_code == 200:
                self.query_json = response.json()
                self.query_id_list = [item['id'] for item in self.query_json['data']]
            else:
                print("Failed to fetch query data")
                return None

    
        #fetch links if needed
        if fetch_links and sighting_id:
            self.sighting_link_url = f"{self.base_url}{sighting_id}/links?fields=id%2Ctenant%2Csubject%2Ctitle%2Cowner%2Cstatus%2Clink_type"
            response = requests.get(self.sighting_link_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=self.headers)
            if response.status_code == 200:
                self.sighting_link_json = response.json()
                #print(linksData)
            else:
                print("Failed to fetch links")
                return None



        #fetch sets if needed
        if fetch_sets and sighting_id:
            self.sighting_sets_url = f"{self.base_url}{sighting_id}/sets?fields=id%2Csubject%2Ctenant%2Ctitle%2Cstatus%2Cowner%2Cfrom_id%2Cfrom_tenant%2Ccomponent"
            response = requests.get(self.sighting_sets_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=self.headers)
            if response.status_code == 200:
                self.sighting_sets_json = response.json()
                #print(linksData)
            else:
                print("Failed to fetch sets")
                return None
            

        #fetch history if needed
        if  fetch_history and sighting_id:
            self.sighting_history_url = f"{self.base_url}{sighting_id}/history?fields=id%2Ctitle%2C%20bug.exposure%2C%20bug.forum%2C%20status%2C%20status_reason%2Cupdated_date%2Crev"
            response = requests.get(self.sighting_history_url, verify='C:/Python313/Lib/site-packages/certifi/cacert.pem', auth=HTTPKerberosAuth(), headers=self.headers)
            if response.status_code == 200:
                self.sighting_history_json = response.json()
                #print(linksData)
            else:
                print("Failed to fetch sets")
                return None



        if fetch_comments and sighting_id:
            return True


    def get_sighting_json(self, sighting_id=None):
        if not sighting_id and sighting_id != self.sighting_id:
            print("⚠️ Warning: The sighting_id provided does not match the one fetched.")
            return None
        if not self.sighting_json:
            print("❌ Error: sighting data not fetched yet. Please call fetch_data() first.")
            return None
        return self.sighting_json
        

    def get_query_json(self, queryId):

        if queryId != self.query_id:
            print(f"⚠️ Warning: The data you fetch is not the same query id")
            return None

        if not self.query_json:
            print("❌ Error: query data not fetched yet. Please call fetch_data() first.")
            return None
        return self.query_json
        
    def get_query_id_list(self, queryId):
        if queryId != self.query_id:
            print(f"⚠️ Warning: The data you fetch is not the same query id")
            return None
        if not self.query_id_list:
            print("❌ Error: query id list not fetched yet. Please call fetch_data() first.")
            return None
        return self.query_id_list
        
    def get_sighting_link_json(self, sighting_id=None):

        if not self.sighting_link_json:
            print(f"⚠️ Warning: Links not fetched yet. Please call fetch_data() first.")
            return None
        return self.sighting_link_json

    def get_sighting_sets_json(self, sighting_id=None):

        if not self.sighting_sets_json:
            print(f"⚠️ Warning: Sets not fetched yet. Please call fetch_data() first.")
            return None
        return self.sighting_sets_json
 
    def get_sighting_field_value(self, field=None):
        if not self.sighting_json:
            print(f"⚠️ Warning: Sets not fetched yet. Please call fetch_data() first.")
            return None
        return self.sighting_json.get("data", [])[0].get(self.get_full_field_name(field)) or ""

    def update_data():
        print("hello")

    def comment_get_id(self):
        return self.sighting_id
    
    def comment_get_value_by_field(self, field_id='parent_id'):
        return self.sighting_json.get('data', [])[0][field_id]


    def get_sighting_history(self):
        return  self.sighting_history_json

def main():
    print("Hello")

if __name__ == "__main__":
    main()
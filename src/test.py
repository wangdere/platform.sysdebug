import requests
from requests.auth import HTTPBasicAuth
import urllib3
import sighting_util as su

#su.wiki_get_page_data()
su.wiki_add_comment_id_to_page("1563621733")
#su.wiki_add_comment_id_to_page("14612563026")
'''
{
    "id": "4260912289",
    "type": "page",
    "status": "current",
    "title": "Informative comments",
    "version": {
        "by": {
            "type": "known",
            "username": "wangdere",
            "userKey": "8a89220957a7e93c0157a7ec52c84640",
            "profilePicture": {
                "path": "/images/icons/profilepics/default.svg",
                "width": 48,
                "height": 48,
                "isDefault": True
            },
            "displayName": "Wang, Dongmin",
            "_links": {
                "self": "https://wiki.ith.intel.com/rest/api/user?key=8a89220957a7e93c0157a7ec52c84640"
            },
            "_expandable": {
                "status": ""
            }
        },
        "when": "2025-07-26T10:00:58.867-07:00",
        "message": "",
        "number": 2,
        "minorEdit": False,
        "hidden": False,
        "_links": {
            "self": "https://wiki.ith.intel.com/rest/experimental/content/4260912289/version/2"
        },
        "_expandable": {
            "content": "/rest/api/content/4260912289"
        }
    },
    "extensions": {
        "position": "none"
    },
    "_links": {
        "webui": "/display/oksdebug/Informative+comments",
        "edit": "/pages/resumedraft.action?draftId=4260912289",
        "tinyui": "/x/oVz4-Q",
        "collection": "/rest/api/content",
        "base": "https://wiki.ith.intel.com",
        "context": "",
        "self": "https://wiki.ith.intel.com/rest/api/content/4260912289"
    },
    "_expandable": {
        "container": "/rest/api/space/oksdebug",
        "metadata": "",
        "operations": "",
        "children": "/rest/api/content/4260912289/child",
        "restrictions": "/rest/api/content/4260912289/restriction/byOperation",
        "history": "/rest/api/content/4260912289/history",
        "ancestors": "",
        "body": "",
        "descendants": "/rest/api/content/4260912289/descendant",
        "space": "/rest/api/space/oksdebug"
    }
}
'''
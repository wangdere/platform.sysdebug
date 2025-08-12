from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any

'''
all returned data is like:

[
  {
    "Forum": "SysDebug.platform.xprod",
    "ID": "15017922934",
    "Title": "[CWF-AP A0][2S][DM][RPP][VIS][A2][D5CU720100279] y-cruncher stress test fail",
    "Exposure": "3-medium",
    "Forum Change": "changed from A to B; updated policy",
    "Justification": "Justification text here"
  },
  {
    "Forum": "SysDebug.platform.yprod",
    "ID": "15017922935",
    "Title": "Another title example",
    "Exposure": "2-low",
    "Forum Change": "removed forum C",
    "Justification": "Another justification"
  },
  ...
]



'''




class BaseReporter(ABC):
    DMR_START_DATE = datetime(2025, 1, 1)

    '''
    All the table in the class is the header (list) + 2 dimentional rows (2 d list): 
    header = ['Categorization', 'Forum', 'ID', 'Title', 'Exposure', 'Scrub Note or Executive Summary']

    [
        ['Cat1', 'Forum1', '12345', 'Example Title', 'High', 'Note1'],
        ['Cat2', 'Forum2', '12346', 'Another Title', 'Low', 'Note2']
    ]
            '''


    def __init__(self):
        pass


    @abstractmethod
    def generate(self, sighting_list, week=None, **kwargs) -> Any:
        """
        所有 reporter 必须实现这个方法。
        **kwargs 根据不同 reporter 可以包含比如 week=int, etc.
    """
        raise NotImplementedError

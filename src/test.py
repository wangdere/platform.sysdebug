import win32com.client
import pandas as pd
import os
import time

# 创建独立 Excel 实例
excel = win32com.client.DispatchEx("Excel.Application")

# Workbooks 对象
workbooks = excel.Workbooks
print('to create url')
# SharePoint 文件 URL
url = "https://intel.sharepoint.com/sites/eaglestreamplatformsysdebug/Shared%20Documents/OKS%20DMR%20Sysdebug/DMR_Sysdebug_working_sheet.xlsm?web=1"

# 打开文件
wb = workbooks.Open(url, ReadOnly=True)

# 读取所有 sheet 到 pandas
sheets_data = {}
for sheet in wb.Sheets:
    data = sheet.UsedRange.Value
    # 转换为 DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    sheets_data[sheet.Name] = df
    print (sheet.Name)

wb.Close(SaveChanges=False)
excel.Quit()
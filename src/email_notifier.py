import win32com.client as win32


class EmailNotifier:
    def __init__(self, subject, to_list=["Wang,Dongmin"], cc_list=None, greeting=None):
        self.outlook = win32.Dispatch("Outlook.Application")
        self.mail = self.outlook.CreateItem(0)
        self.mail.Subject = subject
        self.mail.To = "; ".join(to_list)
        self.mail.CC = "; ".join(cc_list) if cc_list else ""

        self.mail.Display()
        self.inspector = self.mail.GetInspector
        self.word_editor = self.inspector.WordEditor
        self.word_editor.Application.Selection.TypeText(greeting or "Hi team,\n\n")
        self.current_headers = ["id", "title", "status", "exposure", "forum", "comments"]
        self.current_rows = [] 
        self.constants = win32.constants

#    def add_rule_result(self, rule_name, rows):
    def put_description_to_email(self, rule_name):
        sel = self.word_editor.Application.Selection
        sel.TypeText(f"🔍 {rule_name}\n")
        sel.TypeParagraph()

    def add_result_table_header(self, header_list = None):
        if header_list: 
            self.current_headers = header_list
        self.current_rows = []

    def add_rule_result(self, o_hsd_conn, result, message):
        if result is True:
            return 
        row = {}
        for header in self.current_headers:
            value = o_hsd_conn.get_sighting_field_value(header)
            if header == "comments":
                row["comments"] = message or ""
            else:
                row[header] = value    
        self.current_rows.append(row)

    def put_table_to_email(self):
        n_rows = len(self.current_rows) + 1  # header + rows
        n_cols = len(self.current_headers)

        table = self.word_editor.Tables.Add(self.word_editor.Application.Selection.Range, n_rows, n_cols)
        table.Borders.Enable = True

        # 插入 header
        for col, header in enumerate(self.current_headers, start=1):
            table.Cell(1, col).Range.Text = header

        # 插入每一行数据
        for row_idx, row in enumerate(self.current_rows, start=2):
            for col_idx, header in enumerate(self.current_headers, start=1):
                value = row[header]
                cell_range = table.Cell(row_idx, col_idx).Range
                if header == "id":
                    # 插入超链接
                    cell_range.Text = value
                    cell_range.Hyperlinks.Add(Anchor=cell_range, Address=f"https://hsdes.intel.com/appstore/article_legacy/#/{value}", TextToDisplay=cell_range.Text )
                else:
                    cell_range.Text = value
        # ✅ 正确地 collapse 表格 range
        table.Range.Collapse(Direction=0)
        table.Range.InsertParagraphAfter()

        # 将 Selection 移动到当前文档末尾，避免下一张表被插入到当前表格内部
        self.word_editor.Application.Selection.EndKey(Unit=6)  # 6 = wdStory
        self.word_editor.Application.Selection.TypeParagraph()

    
    def put_footer(self, domain_lead_name=""):
        self.word_editor.Application.Selection.EndKey(Unit=6)
        self.word_editor.Application.Selection.TypeParagraph()
        self.word_editor.Application.Selection.TypeText(f"Regards,\n{domain_lead_name or 'Platform debug leads'}")

    def display(self):
        self.mail.Display()

    def send(self):
        self.mail.Send()


    

    #this is for the external caller to simply add one table to email object
    def add_table(self, table_data_dict, table_title: str ):
        #table_data is a 2 D list , first row is the header.

        sel = self.word_editor.Application.Selection
        sel.TypeText(f"{table_title}\n")
        sel.TypeText("\n")  # 空行分隔


        if table_data_dict != []:
            self.current_headers = list(table_data_dict[0].keys())
            self.current_rows = table_data_dict
            
            
            self.put_table_to_email()

        else:
            sel.TypeText("N.A")  # 空行分隔
            sel.TypeText("\n")  # 空行分隔
        sel.EndKey(Unit=6)  # 6 = wdStory
        sel.TypeParagraph()

#example code below
def send_email_via_outlook(to, subject, body, cc=None, attachments=None):
    outlook = win32.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)  # 0: olMailItem

    mail.To = to
    if cc:
        mail.CC = cc
    mail.Subject = subject
    mail.Body = body

    # 添加附件（可选）
    if attachments:
        for file in attachments:
            mail.Attachments.Add(file)

    mail.Send()
    print("✅ Email sent via Outlook.")




def send_outlook_email_with_table():
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = "dongmin.wang@intel.com"
    mail.Subject = "HSDES Summary with Table"

    # 打开编辑器
    mail.Display()
    inspector = mail.GetInspector
    word_editor = inspector.WordEditor

    # 插入段落说明
    word_editor.Application.Selection.TypeText("Hi team,\nPlease check the table below:\n\n")

    # 创建表格（行数=数据+标题行，列数=3）
    num_rows = 3  # 1 header + 2 rows of data
    num_cols = 3
    table = word_editor.Tables.Add(word_editor.Application.Selection.Range, num_rows, num_cols)
    # 添加所有边框
    table.Borders.Enable = True  # 启用边框
    table.Borders.OutsideLineStyle = 1  # 外边框实线
    table.Borders.InsideLineStyle = 1   # 内边框实线
    constants = win32.constants
    # 设置表头
    headers = ["ID", "Title", "Status"]
    for i, h in enumerate(headers):
        cell = table.Cell(1, i+1)
        cell.Range.Text = h
        cell.Range.Bold = True

    # 准备数据
    rows = [
        {"id": "123445", "title": "This is a title", "status": "Open"},
        {"id": "123446", "title": "Another item", "status": "Closed"},
    ]

    # 填写数据
    for row_idx, row in enumerate(rows):
        row_num = row_idx + 2  # 从第2行开始填数据

        # 添加超链接到 ID 列
        link = f"https://hsdes.intel.com/appstore/article_legacy/#/{row['id']}"
        print (link)
        id_cell = table.Cell(row_num, 1)
        id_cell.Range.Text = row["id"]
        id_range = id_cell.Range
        id_range.End = id_range.End - 1  # 避免链接包括最后的换行
        word_editor.Hyperlinks.Add(Anchor=id_range, Address=link,TextToDisplay=id_cell.Range.Text)

        # Title 列
        table.Cell(row_num, 2).Range.Text = row["title"]

        # Status 列，设置颜色
        status_text = row["status"]
        status_cell = table.Cell(row_num, 3)
        status_cell.Range.Text = status_text
        if status_text.lower() == "open":
            status_cell.Range.Font.Color = 0x00FF00 
        else:
           status_cell.Range.Font.Color = 0x0000FF 

    table.Range.Collapse(Direction=0)
    table.Range.InsertParagraphAfter()  # 插入段落（换行）

    # 添加结尾
    word_editor.Application.Selection.EndKey(Unit=6)
    word_editor.Application.Selection.TypeParagraph()
    word_editor.Application.Selection.TypeText("Regards,\nYour Script")

  
    print("✅ Table inserted into Outlook email. Please review and click Send manually.")


import xlwings as xw


app = xw.App(visible= True, add_book=False)

for dept in ["tech", "operation", "finance"] : 
	workbook = app.books.add()
	workbook.save(f"./perf-{dept}.xlsx")
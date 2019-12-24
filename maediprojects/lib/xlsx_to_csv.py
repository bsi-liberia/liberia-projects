import xlrd
import datetime


def getDataFromFile(f, file_contents, sheet, by_id=False, headers_row=0):

    book = xlrd.open_workbook(filename=f, file_contents=file_contents)

    def getData(book, sheet, by_id, headers_row):
        if by_id:
            sheet = book.sheet_by_index(sheet)
        else:
            sheet = book.sheet_by_name(sheet)
        headers = dict( (i, sheet.cell_value(headers_row, i).strip() ) for i in range(sheet.ncols) )

        def makeNiceNumber(val):
            valint = int(val)
            if float(valint) == val:
                return str(valint)
            return str(val)

        def item(i, j):
            val = sheet.cell_value(i,j)
            cell_type = sheet.cell_type(i,j)
            if cell_type == xlrd.XL_CELL_NUMBER:
                val = makeNiceNumber(val)
            elif cell_type == xlrd.XL_CELL_DATE:
                val = datetime.datetime(*xlrd.xldate_as_tuple(val, book.datemode))
                val = val.strftime("%d/%m/%Y")
            elif cell_type == xlrd.XL_CELL_BOOLEAN:
                val = ('FALSE', 'TRUE')[val]
            return (sheet.cell_value(headers_row,j).strip(), val.encode("utf8"))

        out = [ dict(item(i,j) for j in range(sheet.ncols)) \
            for i in range(headers_row+1, sheet.nrows) ]
        return out
    if sheet == "all":
        data = []
        for sheet in range(0,100):
            try:
                data += getData(book, sheet, by_id, headers_row)
            except IndexError:
                break
        return data
    else:
        return getData(book, sheet, by_id, headers_row)

import xlrd, mmap
import codecs
import datetime

def getDataFromFile(f, file_contents, sheet, by_id=False):

    book = xlrd.open_workbook(filename=f, file_contents=file_contents)
    if by_id:
        sheet = book.sheet_by_index(sheet)    
    else:
        sheet = book.sheet_by_name(sheet)
    headers = dict( (i, sheet.cell_value(0, i).strip() ) for i in range(sheet.ncols) )
    
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
        return (sheet.cell_value(0,j).strip(), val.encode("utf8"))

    out = [ dict(item(i,j) for j in range(sheet.ncols)) \
        for i in range(1, sheet.nrows) ]
    return out

from io import BytesIO

from openpyxl import load_workbook


def getDataFromFile(f, file_contents, sheetname, by_id=False, headers_row=0):

    if file_contents:
        f = BytesIO(file_contents)
    book = load_workbook(filename=f, read_only=True)

    def getData(book, sheetname, by_id, headers_row):
        if by_id:
            sheet = book[book.sheetnames[sheetname]]
        else:
            sheet = book[sheetname]

        rows = list(sheet.rows)[headers_row:]
        first_row = [cell.value for cell in rows[0]]
        data = []
        for row in rows[1:]:
            record = {}
            for key, cell in zip(first_row, row):
                if cell.data_type == 's':
                    record[key] = cell.value.strip()
                else:
                    record[key] = cell.value
            data.append(record)
        return data
    if sheetname == "all":
        data = []
        for _sheetname in book.sheetnames:
            try:
                data += getData(book, _sheetname, False, headers_row)
            except IndexError:
                break
        return data
    else:
        return getData(book, sheetname, by_id, headers_row)

from openpyxl.worksheet.datavalidation import DataValidation
from maediprojects.lib.codelists import get_codelists_lookups_by_name

# Activity Status validation
v_status = DataValidation(type="list", allow_blank=False)
v_status.error ='Your entry is not in the list'
v_status.errorTitle = 'Activity Status'
v_status.prompt = 'Please select from the list'
v_status.promptTitle = 'Activity Status'

# ID validation
v_id = DataValidation(type="whole")
v_id.errorTitle = "Invalid ID"
v_id.error = "Please enter a valid ID"
v_id.promptTitle = 'Liberia Project Dashboard ID'
v_id.prompt = 'Please do not edit this ID. It is used by the Liberia Project Dashboard to uniquely identify activities.'

# Date validation
v_date = DataValidation(type="date")
v_date.errorTitle = "Invalid date"
v_date.error = "Please enter a valid date"

# Number validation
v_number = DataValidation(type="decimal")
v_number.errorTitle = "Invalid number"
v_number.error = "Please enter a valid number"

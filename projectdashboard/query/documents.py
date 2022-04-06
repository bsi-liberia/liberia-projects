from projectdashboard import models
from projectdashboard.extensions import db
import os
import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from flask_login import current_user


def add_document(activity_id, title, category_codes, file):
    datetime_now = datetime.datetime.utcnow()
    safe_timestamp = secure_filename(datetime_now.isoformat())
    safe_filename = secure_filename(file.filename)
    filename = f"{safe_timestamp}-{safe_filename}"
    filename_to_save = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filename_to_save)
    filesize = os.stat(filename_to_save).st_size
    document = models.ActivityDocumentLink()
    document.activity_id = activity_id
    document.title = title
    document.local = True
    document.filename = filename
    document.original_filename = safe_filename
    document.saved_datetime = datetime_now
    document.filesize = filesize
    category = models.ActivityDocumentLinkCategory()
    for category_code in category_codes:
        category.code = category_code
        document.categories.append(category)
    db.session.add(document)
    db.session.commit()
    return document

# -*- coding: utf-8 -*-
__title__   = "Lock"
__doc__     = """Version = 1.0
Date    = 29.04.2025
________________________________________________________________
Description:


________________________________________________________________
Author: Zwe"""

from pyrevit import revit, DB, forms, script
import hashlib

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def set_lock_parameter(element, password_hash):
    param = element.LookupParameter("PyRevitLockHash")
    if param and param.StorageType == DB.StorageType.String:
        param.Set(password_hash)

# Ask user for password
password = forms.ask_for_string(
    prompt="Enter password to lock elements:",
    title="Lock Elements",
    default=""
)

if not password:
    forms.alert("No password entered. Lock cancelled.")
    script.exit()

password_hash = get_password_hash(password)

with revit.Transaction("Lock Elements with Password"):
    for el in revit.get_selection():
        el.Pinned = True
        set_lock_parameter(el, password_hash)

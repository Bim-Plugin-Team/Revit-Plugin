# -*- coding: utf-8 -*-
__title__   = "Unlock"
__doc__     = """Version = 1.0
Date    = 22.04.2025
________________________________________________________________
Description:

To Unlock Elements
________________________________________________________________
How-To:

________________________________________________________________
Last Updates:
- [22.04.2025] v1.0 Release
________________________________________________________________
Author: Zwe"""

from pyrevit import revit, DB, forms, script
import hashlib

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_lock_parameter(element):
    param = element.LookupParameter("PyRevitLockHash")
    if param and param.HasValue:
        return param.AsString()
    return None

# Ask user for password
password = forms.ask_for_string(
    prompt="Enter password to unlock elements:",
    title="Unlock Elements",
    default=""
)

if not password:
    forms.alert("No password entered. Unlock cancelled.")
    script.exit()

password_hash = get_password_hash(password)

with revit.Transaction("Unlock Elements with Password"):
    for el in revit.get_selection():
        lock_hash = get_lock_parameter(el)
        if lock_hash == password_hash:
            el.Pinned = False
            param = el.LookupParameter("PyRevitLockHash")
            if param:
                param.Set("")
        else:
            forms.alert("Wrong password for one or more elements. They will remain pinned.", title="Access Denied")


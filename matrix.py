#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import random
import string
import requests

# -------------------------
# Wrapper: Check if STDIN has JSON (Enterprise mode)
# -------------------------
if not os.environ.get("NOTIFY_HOSTNAME"):
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit("ERROR: Keine gültigen JSON-Daten von STDIN erhalten und keine Umgebungsvariablen verfügbar.")

    context = input_data.get("context", {})
    params = input_data.get("parameters", {})

    # Setze alte Umgebungsvariablen
    for k, v in context.items():
        os.environ[k] = v or ""
    os.environ["NOTIFY_PARAMETER_1"] = params.get("parameter_1", "")
    os.environ["NOTIFY_PARAMETER_2"] = params.get("parameter_2", "")
    os.environ["NOTIFY_PARAMETER_3"] = params.get("parameter_3", "")

# -------------------------
# Dein Originalskript (angepasst für .get())
# -------------------------

MATRIXHOST = os.environ.get("NOTIFY_PARAMETER_1", "")
MATRIXTOKEN = os.environ.get("NOTIFY_PARAMETER_2", "")
MATRIXROOM = os.environ.get("NOTIFY_PARAMETER_3", "")

data = {
    "TS": os.environ.get("NOTIFY_SHORTDATETIME", ""),

    # Host related info.
    "HOST": os.environ.get("NOTIFY_HOSTNAME", ""),
    "HOSTADDR": os.environ.get("NOTIFY_HOSTADDRESS", ""),
    "HOSTSTATE": os.environ.get("NOTIFY_HOSTSTATE", ""),
    "HOSTSTATEPREVIOUS": os.environ.get("NOTIFY_LASTHOSTSTATE", ""),
    "HOSTSTATECOUNT": os.environ.get("NOTIFY_HOSTNOTIFICATIONNUMBER", ""),
    "HOSTOUTPUT": os.environ.get("NOTIFY_HOSTOUTPUT", ""),

    # Service related info.
    "SERVICE": os.environ.get("NOTIFY_SERVICEDESC", ""),
    "SERVICESTATE": os.environ.get("NOTIFY_SERVICESTATE", ""),
    "SERVICESTATEPREVIOUS": os.environ.get("NOTIFY_LASTSERVICESTATE", ""),
    "SERVICESTATECOUNT": os.environ.get("NOTIFY_SERVICENOTIFICATIONNUMBER", ""),
    "SERVICEOUTPUT": os.environ.get("NOTIFY_SERVICEOUTPUT", "")
}

servicemessage = '''Service <b>{SERVICE}</b> at <b>{HOST}</b> ({HOSTADDR}) | TS: {TS} | STATE: <b>{SERVICESTATE}</b>
<br>{SERVICEOUTPUT}<br>'''

hostmessage = '''Host <b>{HOST}</b> ({HOSTADDR}) | TS: {TS} | STATE: <b>{HOSTSTATE}</b>
<br>{HOSTOUTPUT}<br>'''

message = ""

print(data)

# Checking host status first.
if (data["HOSTSTATE"] != data["HOSTSTATEPREVIOUS"] or data["HOSTSTATECOUNT"] != "0"):
    message = hostmessage.format(**data)

# Check service state.
if (data["SERVICE"] and data["SERVICE"] != "$SERVICEDESC$") and \
   (data["SERVICESTATE"] != data["SERVICESTATEPREVIOUS"] or data["SERVICESTATECOUNT"] != "0"):
    message = servicemessage.format(**data)

# Data we will send to Matrix Homeserver.
matrixDataDict = {
    "msgtype": "m.text",
    "body": message,
    "format": "org.matrix.custom.html",
    "formatted_body": message,
}
matrixData = json.dumps(matrixDataDict).encode("utf-8")

# Random transaction ID for Matrix Homeserver.
txnId = ''.join(random.SystemRandom().choice(
    string.ascii_uppercase + string.digits) for _ in range(16))

matrixHeaders = {
    "Authorization": "Bearer " + MATRIXTOKEN,
    "Content-Type": "application/json",
    "Content-Length": str(len(matrixData))
}

# Request.
try:
    req = requests.put(
        url=MATRIXHOST + "/_matrix/client/r0/rooms/" + MATRIXROOM + "/send/m.room.message/" + txnId,
        data=matrixData,
        headers=matrixHeaders
    )
    print(f"Matrix API Response: {req.status_code} {req.text}", file=sys.stderr)
except Exception as e:
    print(f"ERROR: Matrix-Sendeproblem: {e}", file=sys.stderr)
    sys.exit(1)

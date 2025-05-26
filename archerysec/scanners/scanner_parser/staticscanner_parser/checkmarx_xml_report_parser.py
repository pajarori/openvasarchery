# -*- coding: utf-8 -*-
#                    _
#     /\            | |
#    /  \   _ __ ___| |__   ___ _ __ _   _
#   / /\ \ | '__/ __| '_ \ / _ \ '__| | | |
#  / ____ \| | | (__| | | |  __/ |  | |_| |
# /_/    \_\_|  \___|_| |_|\___|_|   \__, |
#                                     __/ |
#                                    |___/
# Copyright (C) 2017 Anand Tiwari
#
# Email:   anandtiwarics@gmail.com
# Twitter: @anandtiwarics
#
# This file is part of ArcherySec Project.

import hashlib
import uuid
from datetime import datetime

from archeryapi.models import OrgAPIKey
from dashboard.views import trend_update
from staticscanners.models import StaticScanResultsDb, StaticScansDb
from utility.email_notify import email_sch_notify

vul_col = ""
severity = ""
project = ""
result = ""
result_data = ""
file_name = ""
inst = ""
code_data = ""


def checkmarx_report_xml(data, project_id, scan_id, request):
    """

    :param data:
    :param project_id:
    :param scan_id:
    :return:
    """
    date_time = datetime.now()

    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization
    global vul_col, project, result, result_data, file_name, inst, code_data
    project = data.attrib["ProjectName"]
    scan_details = data.attrib
    for dat in data:
        # query = dat.attrib
        name = dat.attrib["name"]
        severity = dat.attrib["Severity"]
        code_data = []
        result_data_all = []
        for dd in dat:
            result_data = dd.attrib
            file_name = dd.attrib["FileName"]
            result_data_all.append(dd.attrib)
            for d in dd.findall(".//Code"):
                result = d.text
                instance = {}
                instance[file_name] = d.text
                code_data.append(instance)
        if severity == "Critical":
            vul_col = "critical"
        elif severity == "High":
            vul_col = "danger"
        elif severity == "Medium":
            vul_col = "warning"
        elif severity == "Low":
            vul_col = "info"
        else:
            severity = "Low"
            vul_col = "info"
        vul_id = uuid.uuid4()

        dup_data = str(name) + str(severity) + str(file_name)
        duplicate_hash = hashlib.sha256(dup_data.encode("utf-8")).hexdigest()
        match_dup = StaticScanResultsDb.objects.filter(
            dup_hash=duplicate_hash, organization=organization
        ).values("dup_hash")
        lenth_match = len(match_dup)
        if lenth_match == 0:
            duplicate_vuln = "No"

            false_p = StaticScanResultsDb.objects.filter(
                false_positive_hash=duplicate_hash,
                organization=organization,
            )
            fp_lenth_match = len(false_p)
            if fp_lenth_match == 1:
                false_positive = "Yes"
            else:
                false_positive = "No"

            save_all = StaticScanResultsDb(
                vuln_id=vul_id,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                severity_color=vul_col,
                vuln_status="Open",
                dup_hash=duplicate_hash,
                vuln_duplicate=duplicate_vuln,
                false_positive=false_positive,
                title=name,
                severity=severity,
                description=str(scan_details),
                fileName=file_name,
                scanner="Checkmarx",
                organization=organization,
            )
            save_all.save()

        else:
            duplicate_vuln = "Yes"

            save_all = StaticScanResultsDb(
                vuln_id=vul_id,
                scan_id=scan_id,
                date_time=date_time,
                project_id=project_id,
                severity_color=vul_col,
                vuln_status="Duplicate",
                dup_hash=duplicate_hash,
                vuln_duplicate=duplicate_vuln,
                false_positive="Duplicate",
                title=name,
                severity=severity,
                description=str(scan_details),
                fileName=file_name,
                scanner="Checkmarx",
                organization=organization,
            )
            save_all.save()

    all_findbugs_data = StaticScanResultsDb.objects.filter(
        scan_id=scan_id, false_positive="No", organization=organization
    )

    duplicate_count = StaticScanResultsDb.objects.filter(
        scan_id=scan_id, vuln_duplicate="Yes", organization=organization
    )

    total_critical = len(all_findbugs_data.filter(severity="Critical"))
    total_high = len(all_findbugs_data.filter(severity="High"))
    total_medium = len(all_findbugs_data.filter(severity="Medium"))
    total_low = len(all_findbugs_data.filter(severity="Low"))
    total_vul = len(all_findbugs_data)
    total_duplicate = len(duplicate_count.filter(vuln_duplicate="Yes"))

    StaticScansDb.objects.filter(scan_id=scan_id).update(
        project_name=project,
        date_time=date_time,
        total_vul=total_vul,
        critical_vul=total_critical,
        high_vul=total_high,
        medium_vul=total_medium,
        low_vul=total_low,
        total_dup=total_duplicate,
        scanner="Checkmarx",
        organization=organization,
    )
    trend_update()
    subject = "Archery Tool Scan Status - checkmarx Report Uploaded"
    message = (
        "checkmarx Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s"
        % ("checkmarx", total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "checkmarx": {
        "displayName": "Checkmarx",
        "dbtype": "StaticScans",
        "dbname": "Checkmarx",
        "type": "XML",
        "parserFunction": checkmarx_report_xml,
        "icon": "/static/tools/checkmarx.png",
    }
}

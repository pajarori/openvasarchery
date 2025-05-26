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
Target = ""
VulnerabilityID = ""
PkgName = ""
InstalledVersion = ""
FixedVersion = ""
Title = ""
Description = ""
severity = ""
References = ""
false_positive = ""


def brakeman_report_json(data, project_id, scan_id, request):
    """

    :param data:
    :param project_id:
    :param scan_id:
    :return:
    :username:
    """
    global false_positive
    date_time = datetime.now()
    vul_col = ""

    # Parser for above json data
    # print(data['warnings'])

    vuln = data["warnings"]
    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization
    for vuln_data in vuln:
        try:
            name = vuln_data["warning_type"]
        except Exception:
            name = "Not Found"

        # try:
        #    warning_code = vuln_data["warning_code"]
        # except Exception:
        #     warning_code = "Not Found"

        # try:
        #     fingerprint = vuln_data["fingerprint"]
        # except Exception:
        #     fingerprint = "Not Found"

        try:
            description = vuln_data["message"]
        except Exception:
            description = "Not Found"

        # try:
        #     check_name = vuln_data["check_name"]
        # except Exception:
        #     check_name = "Not Found"

        try:
            severity = vuln_data["confidence"]
            if severity == "Weak":
                severity = "Low"
        except Exception:
            severity = "Not Found"

        try:
            file = vuln_data["file"]
        except Exception:
            file = "Not Found"

        # try:
        #     line = vuln_data["line"]
        # except Exception:
        #     line = "Not Found"

        try:
            link = vuln_data["link"]
        except Exception:
            link = "Not Found"

        try:
            code = vuln_data["code"]
        except Exception:
            code = "Not Found"

        try:
            render_path = vuln_data["render_path"]
        except Exception:
            render_path = "Not Found"

        if severity == "Critical":
            vul_col = "critical"

        if severity == "High":
            vul_col = "danger"

        elif severity == "Medium":
            vul_col = "warning"

        elif severity == "Low":
            vul_col = "info"

        elif severity == "Unknown":
            severity = "Low"
            vul_col = "info"

        elif severity == "Everything else":
            severity = "Low"
            vul_col = "info"

        vul_id = uuid.uuid4()

        dup_data = str(name) + str(severity) + str(file)

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
                description=str(description)
                + "\n\n"
                + str(code)
                + "\n\n"
                + str(render_path),
                severity=severity,
                fileName=file,
                references=link,
                scanner="Brakeman_scan",
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
                description=str(description)
                + "\n\n"
                + str(code)
                + "\n\n"
                + str(render_path),
                severity=severity,
                fileName=file,
                references=link,
                scanner="Brakeman_scan",
                organization=organization,
            )
            save_all.save()

    all_findbugs_data = StaticScanResultsDb.objects.filter(
        scan_id=scan_id,
        false_positive="No",
        vuln_duplicate="No",
        organization=organization,
    )

    duplicate_count = StaticScanResultsDb.objects.filter(
        scan_id=scan_id, vuln_duplicate="Yes", organization=organization
    )

    total_vul = len(all_findbugs_data)
    total_critical = len(all_findbugs_data.filter(severity="Critical"))
    total_high = len(all_findbugs_data.filter(severity="High"))
    total_medium = len(all_findbugs_data.filter(severity="Medium"))
    total_low = len(all_findbugs_data.filter(severity="Low"))
    total_duplicate = len(duplicate_count.filter(vuln_duplicate="Yes"))

    StaticScansDb.objects.filter(scan_id=scan_id).update(
        date_time=date_time,
        total_vul=total_vul,
        critical_vul=total_critical,
        high_vul=total_high,
        medium_vul=total_medium,
        low_vul=total_low,
        total_dup=total_duplicate,
        scanner="Brakeman_scan",
        organization=organization,
    )
    trend_update()
    subject = "Archery Tool Scan Status - brakeman Report Uploaded"
    message = (
        "brakeman Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s"
        % (Target, total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "brakeman": {
        "displayName": "brakeman Scanner",
        "dbtype": "StaticScans",
        "dbname": "Brakeman_scan",
        "type": "JSON",
        "parserFunction": brakeman_report_json,
        "icon": "/static/tools/brakeman.png",
    }
}

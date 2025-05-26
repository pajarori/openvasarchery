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


def whitesource_report_json(data, project_id, scan_id, request):
    """

    :param data:
    :param project_id:
    :param scan_id:
    :return:
    """
    date_time = datetime.now()

    global vul_col, project
    vuln = data["vulnerabilities"]

    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization

    for issues in vuln:
        name = issues["name"]
        severity = issues["severity"]
        score = issues["score"]
        # cvss3_severity = issues["cvss3_severity"]
        # cvss3_score = issues["cvss3_score"]
        # publishDate = issues["publishDate"]
        # lastUpdatedDate = issues["lastUpdatedDate"]
        # scoreMetadataVector = issues["scoreMetadataVector"]
        url = issues["url"]
        description = issues["description"]
        project = issues["project"]
        # product = issues["product"]
        # cvss3Attributes = issues["cvss3Attributes"]
        library = issues["library"]
        topFix = issues["topFix"]
        # allFixes = issues['allFixes']
        filename = issues["library"]["filename"]
        # sha1 = issues["library"]["sha1"]
        # version = issues["library"]["version"]
        # groupId = issues["library"]["groupId"]
        if severity == "critical":
            severity = "Critical"
            vul_col = "critical"
        elif severity == "high":
            severity = "High"
            vul_col = "danger"
        elif severity == "medium":
            severity = "Medium"
            vul_col = "warning"
        elif severity == "low":
            severity = "Low"
            vul_col = "info"
        vul_id = uuid.uuid4()
        dup_data = str(name) + str(severity) + str(project)
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
                references=url,
                description=str(description)
                + "\n\n"
                + str(score)
                + "\n\n"
                + str(library)
                + "\n\n"
                + str(topFix)
                + "\n\n",
                fileName=filename,
                scanner="Whitesource",
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
                references=url,
                description=str(description)
                + "\n\n"
                + str(score)
                + "\n\n"
                + str(library)
                + "\n\n"
                + str(topFix)
                + "\n\n",
                fileName=filename,
                scanner="Whitesource",
                organization=organization,
            )
            save_all.save()

    all_findbugs_data = StaticScanResultsDb.objects.filter(
        scan_id=scan_id, false_positive="No", organization=organization
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
        project_name=project,
        date_time=date_time,
        total_vul=total_vul,
        critical_vul=total_critical,
        high_vul=total_high,
        medium_vul=total_medium,
        low_vul=total_low,
        total_dup=total_duplicate,
        scanner="Whitesource",
        organization=organization,
    )
    trend_update()
    subject = "Archery Tool Scan Status - whitesource Report Uploaded"
    message = (
        "whitesource Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s"
        % ("whitesource", total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "whitesource": {
        "displayName": "Whitesource Scanner",
        "dbtype": "StaticScans",
        "dbname": "Whitesource",
        "type": "JSON",
        "parserFunction": whitesource_report_json,
        "icon": "/static/tools/whitesource.png",
    }
}

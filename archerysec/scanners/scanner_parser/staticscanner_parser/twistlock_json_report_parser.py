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
Severity = ""
References = ""
false_positive = ""


def twistlock_report_json(data, project_id, scan_id, request):
    """

    :param data:
    :param project_id:
    :param scan_id:
    :return:
    """

    """
    {
    "results": [
        {
            "id": "sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "distro": "Debian GNU/Linux 9 (stretch)",
            "compliances": [
                {
                    "title": "Sensitive information provided in environment variables",
                    "severity": "high",
                    "cause": "The environment variables DD_CELERY_BROKER_PASSWORD,DD_DATABASE_PASSWORD,DD_SECRET_KEY contain sensitive data"
                }
            ],
            "complianceDistribution": {
                "critical": 0,
                "high": 1,
                "medium": 0,
                "low": 0,
                "total": 1
            },
            "vulnerabilities": [
                {
                    "id": "CVE-2013-7459",
                    "cvss": 9.8,
                    "vector": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    "description": "Heap-based buffer overflow in the ALGnew function in block_templace.c in Python Cryptography Toolkit (aka pycrypto) allows remote attackers to execute arbitrary code as demonstrated by a crafted iv parameter to cryptmsg.py.",
                    "severity": "critical",
                    "packageName": "pycrypto",
                    "packageVersion": "2.6.1",
                    "link": "https://web.nvd.nist.gov/view/vuln/detail?vulnId=CVE-2013-7459",
                    "riskFactors": {
                        "Attack complexity: low": {},
                        "Attack vector: network": {},
                        "Critical severity": {},
                        "Remote execution": {}
                    }
                }
            ],
            "vulnerabilityDistribution": {
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0,
                "total": 1
            }
        }
    ]
    }
    """
    global false_positive
    date_time = datetime.now()
    vul_col = ""

    # Parser for above json data

    vuln = data["results"][0]["vulnerabilities"]

    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization

    for vuln_data in vuln:
        try:
            name = vuln_data["id"]
        except Exception:
            name = "Not Found"

        try:
            cvss = vuln_data["cvss"]
        except Exception:
            cvss = "Not Found"

        # try:
        #     vector = vuln_data["vector"]
        # except Exception:
        #     vector = "Not Found"

        try:
            description = vuln_data["description"]
        except Exception:
            description = "Not Found"

        try:
            severity = vuln_data["severity"]
        except Exception:
            severity = "Not Found"

        try:
            packageName = vuln_data["packageName"]
        except Exception:
            packageName = "Not Found"

        try:
            packageVersion = vuln_data["packageVersion"]
        except Exception:
            packageVersion = "Not Found"

        try:
            link = vuln_data["link"]
        except Exception:
            link = "Not Found"

        if severity == "critical":
            severity = "Critical"
            vul_col = "critical"

        if severity == "high":
            severity = "High"
            vul_col = "danger"

        elif severity == "medium":
            severity = "Medium"
            vul_col = "warning"

        elif severity == "low":
            severity = "Low"
            vul_col = "info"

        elif severity == "Unknown":
            severity = "Low"
            vul_col = "info"

        elif severity == "Everything else":
            severity = "Low"
            vul_col = "info"

        vul_id = uuid.uuid4()

        dup_data = str(name) + str(severity) + str(packageName)

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
                + str(cvss)
                + "\n\n"
                + str(packageVersion),
                severity=severity,
                fileName=packageName,
                references=link,
                scanner="Twistlock",
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
                + str(cvss)
                + "\n\n"
                + str(packageVersion),
                severity=severity,
                fileName=packageName,
                references=link,
                scanner="Twistlock",
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

    StaticScansDb.objects.filter(
        scan_id=scan_id, organization=organization
    ).update(
        date_time=date_time,
        total_vul=total_vul,
        critical_vul=total_critical,
        high_vul=total_high,
        medium_vul=total_medium,
        low_vul=total_low,
        total_dup=total_duplicate,
        scanner="Twistlock",
        organization=organization,
    )
    trend_update()
    subject = "Archery Tool Scan Status - twistlock Report Uploaded"
    message = (
        "twistlock Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s"
        % (Target, total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "twistlock": {
        "displayName": "twistlock Scanner",
        "dbtype": "StaticScans",
        "dbname": "Twistlock",
        "type": "JSON",
        "parserFunction": twistlock_report_json,
        "icon": "/static/tools/twistlock.png",
    }
}

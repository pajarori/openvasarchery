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
from utility.email_notify import email_sch_notify
from webscanners.models import WebScanResultsDb, WebScansDb

name = ""
description = ""
remedy_guidance = ""
remedy_code = ""
severity = ""
check = ""
digest = ""
vector = ""
remarks = ""
page = ""
signature = ""
proof = ""
trusted = ""
platform_type = ""
platform_name = ""

url = ""
action = ""
body = ""
vuln_id = ""
vul_col = ""
ref_key = ""
ref_values = ""
vector_input_key = ""
vector_input_values = ""
vector_source_key = ""
vector_source_values = ""
page_body_data = ""
request_url = ""
request_method = ""
request_raw = ""
response_ip = ""
response_raw_headers = ""
false_positive = None


def xml_parser(root, project_id, scan_id, request):
    date_time = datetime.now()
    global name, description, remedy_guidance, remedy_code, severity, check, digest, references, vector, remarks, page, signature, proof, trusted, platform_type, platform_name, url, action, body, vuln_id, vul_col, ref_key, ref_values, vector_input_key, vector_input_values, vector_source_key, vector_source_values, page_body_data, request_url, request_method, request_raw, response_ip, response_raw_headers
    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization
    for issue in root:
        for data in issue:
            if data.tag == "issue":
                for vuln in data:
                    vuln_id = uuid.uuid4()

                    if vuln.tag == "name":
                        if vuln.text is None:
                            name = "NA"
                        else:
                            name = vuln.text
                    if vuln.tag == "description":
                        if vuln.text is None:
                            description = "NA"
                        else:
                            description = vuln.text
                    if vuln.tag == "remedy_guidance":
                        if vuln.text is None:
                            remedy_guidance = "NA"
                        else:
                            remedy_guidance = vuln.text
                    if vuln.tag == "severity":
                        if vuln.text is None:
                            severity = "NA"
                        else:
                            severity = vuln.text

                    if vuln.tag == "references":
                        for ref_vuln in vuln:
                            dat = ref_vuln.attrib
                            for key, values in dat.items():
                                if key is None:
                                    ref_key = "NA"
                                else:
                                    ref_key = key

                                if values is None:
                                    ref_values = "NA"
                                else:
                                    ref_values = values

                    if vuln.tag == "vector":
                        for vec_vuln in vuln:
                            if vec_vuln.tag == "inputs":
                                for vec_input in vec_vuln:
                                    dat = vec_input.attrib
                                    for key, values in dat.items():
                                        if key is None:
                                            vector_input_key = "NA"
                                        else:
                                            vector_input_key = key

                                        if values is None:
                                            vector_input_values = "NA"
                                        else:
                                            vector_input_values = values
                            if vec_vuln.tag == "source":
                                for vec_source in vec_vuln:
                                    source_dat = vec_source.attrib
                                    for key, values in source_dat.items():
                                        if key is None:
                                            vector_source_key = "NA"
                                        else:
                                            vector_source_key = key

                                        if values in None:
                                            vector_source_values = "NA"
                                        else:
                                            vector_source_values = values

                    if vuln.tag == "page":
                        for page_body in vuln:
                            if page_body.tag == "body":
                                page_body_dat = page_body.text

                                if page_body_dat is None:
                                    page_body_data = "NA"
                                else:
                                    page_body_data = page_body_dat
                        for req in vuln:
                            if req.tag == "request":
                                for req_dat in req:
                                    if req_dat.tag == "url":
                                        req_url = req_dat.text
                                        if req_url is None:
                                            request_url = "NA"
                                        else:
                                            request_url = req_url
                                    if req_dat.tag == "method":
                                        req_method = req_dat.text
                                        if req_method is None:
                                            request_method = "NA"
                                        else:
                                            request_method = req_method

                                    if req_dat.tag == "raw":
                                        if req_dat.text is None:
                                            request_raw = "NA"
                                        else:
                                            request_raw = req_dat.text
                            if req.tag == "response":
                                for res_dat in req:
                                    if res_dat.tag == "ip_address":
                                        res_ip = res_dat.text
                                        if res_ip is None:
                                            response_ip = "NA"
                                        else:
                                            response_ip = res_dat.text

                                    if res_dat.tag == "raw_headers":
                                        res_raw_headers = res_dat.text
                                        if res_raw_headers is None:
                                            response_raw_headers = "NA"
                                        else:
                                            response_raw_headers = res_dat.text

                    if vuln.tag == "proof":
                        proof = vuln.text
                        if vuln.text is None:
                            proof = "NA"
                        else:
                            proof = vuln.text

                    for extra_data in vuln:
                        for extra_vuln in extra_data:
                            if extra_vuln.tag == "url":
                                if extra_vuln.text is None:
                                    url = "NA"
                                else:
                                    url = extra_vuln.text
                            if extra_vuln.tag == "action":
                                if extra_vuln.text is None:
                                    action = "NA"
                                else:
                                    action = extra_vuln.text
                            if extra_vuln.tag == "body":
                                if extra_vuln.text is None:
                                    body = "NA"
                                else:
                                    body = extra_vuln.text

                details = (
                    description
                    + "\n\n"
                    + str(proof)
                    + "\n\n"
                    + str(ref_values)
                    + "\n\n"
                    + str(page_body_data)
                )

                dup_data = name + url + severity
                duplicate_hash = hashlib.sha256(dup_data.encode("utf-8")).hexdigest()

                match_dup = (
                    WebScanResultsDb.objects.filter(
                        vuln_duplicate=duplicate_hash,
                        scanner="Arachni",
                        organization=organization,
                    )
                    .values("dup_hash")
                    .distinct()
                )
                lenth_match = len(match_dup)
                if severity == "critical":
                    vul_col = "critical"
                    severity = "Critical"

                elif severity == "high":
                    vul_col = "danger"
                    severity = "High"

                elif severity == "medium":
                    vul_col = "warning"
                    severity = "Medium"

                elif severity == "low":
                    severity = "Low"
                    vul_col = "info"

                else:
                    severity = "Low"
                    vul_col = "info"

                if lenth_match == 0:
                    duplicate_vuln = "No"

                    false_p = WebScanResultsDb.objects.filter(
                        false_positive_hash=duplicate_hash,
                        organization=organization,
                    )
                    fp_lenth_match = len(false_p)

                    global false_positive
                    if fp_lenth_match == 1:
                        false_positive = "Yes"
                    elif fp_lenth_match == 0:
                        false_positive = "No"
                    else:
                        false_positive = "No"

                    dump_data = WebScanResultsDb(
                        vuln_id=vuln_id,
                        scan_id=scan_id,
                        date_time=date_time,
                        severity_color=vul_col,
                        project_id=project_id,
                        title=name,
                        description=details,
                        solution=remedy_guidance,
                        severity=severity,
                        url=url,
                        false_positive=false_positive,
                        vuln_status="Open",
                        false_positive_hash=duplicate_hash,
                        vuln_duplicate=duplicate_vuln,
                        scanner="Arachni",
                        organization=organization,
                    )
                    dump_data.save()

                else:
                    duplicate_vuln = "Yes"

                    dump_data = WebScanResultsDb(
                        vuln_id=vuln_id,
                        scan_id=scan_id,
                        date_time=date_time,
                        severity_color=vul_col,
                        project_id=project_id,
                        title=name,
                        description=details,
                        solution=remedy_guidance,
                        severity=severity,
                        url=url,
                        false_positive="Duplicate",
                        vuln_status="Duplicate",
                        false_positive_hash=duplicate_hash,
                        vuln_duplicate=duplicate_vuln,
                        scanner="Arachni",
                        organization=organization,
                    )
                    dump_data.save()

    arachni_all_vul = WebScanResultsDb.objects.filter(
        scan_id=scan_id,
        false_positive="No",
        scanner="Arachni",
        organization=organization,
    )

    duplicate_count = WebScanResultsDb.objects.filter(
        scan_id=scan_id,
        vuln_duplicate="Yes",
        scanner="Arachni",
        organization=organization,
    )

    total_critical = len(arachni_all_vul.filter(severity="Critical"))
    total_high = len(arachni_all_vul.filter(severity="High"))
    total_medium = len(arachni_all_vul.filter(severity="Medium"))
    total_low = len(arachni_all_vul.filter(severity="Low"))
    total_info = len(arachni_all_vul.filter(severity="Informational"))
    total_duplicate = len(duplicate_count.filter(vuln_duplicate="Yes"))
    total_vul = total_high + total_medium + total_low + total_info

    print(total_high)
    print(total_low)
    print(total_medium)
    print(total_info)

    WebScansDb.objects.filter(
        scan_id=scan_id, organization=organization
    ).update(
        scan_url=url,
        total_vul=total_vul,
        date_time=date_time,
        critical_vul=total_critical,
        high_vul=total_high,
        medium_vul=total_medium,
        low_vul=total_low,
        info_vul=total_info,
        scan_status="100",
        total_dup=total_duplicate,
        scanner="Arachni",
        organization=organization,
    )
    trend_update()

    subject = "Archery Tool Scan Status - Arachni Report Uploaded"
    message = (
        "Arachni Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s" % (url, total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "arachni": {
        "displayName": "Arachni Scanner",
        "dbtype": "WebScans",
        "dbname": "Arachni",
        "type": "XML",
        "parserFunction": xml_parser,
        "icon": "/static/tools/arachni.png",
    }
}

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


import uuid

from archeryapi.models import OrgAPIKey
from compliance.models import InspecScanDb, InspecScanResultsDb
from utility.email_notify import email_sch_notify

status = None
controls_results_message = None


def inspec_report_json(data, project_id, scan_id, request):
    """

    :param data:
    :param project_id:
    :param scan_id:
    :return:
    """
    global controls_results_message, status
    vul_col = "info"
    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization
    for key, value in data.items():
        if key == "profiles":
            for profile in value:
                controls = profile["controls"]
                for con in controls:
                    controls_id = con["id"]
                    controls_title = con["title"]
                    controls_desc = con["desc"]
                    controls_descriptions = con["descriptions"][0]["data"]
                    controls_impact = con["impact"]
                    controls_refs = con["refs"]
                    controls_tags_severity = con["tags"]["severity"]
                    controls_tags_cis_id = con["tags"]["cis_id"]
                    controls_tags_cis_control = con["tags"]["cis_control"]
                    controls_tags_cis_level = con["tags"]["cis_level"]
                    controls_tags_audit = con["tags"]["audit text"]
                    controls_tags_fix = con["tags"]["fix"]
                    controls_code = con["code"]
                    controls_source_location = con["source_location"]["line"]
                    for res in con["results"]:
                        controls_results_status = res["status"]
                        controls_results_code_desc = res["code_desc"]
                        controls_results_run_time = res["run_time"]
                        controls_results_start_time = res["start_time"]
                        for key, value in res.items():
                            if key == "message":
                                controls_results_message = value

                        if controls_results_status == "failed":
                            vul_col = "danger"
                            status = "Failed"

                        elif controls_results_status == "passed":
                            vul_col = "warning"
                            status = "Passed"

                        elif controls_results_status == "skipped":
                            vul_col = "info"
                            status = "Skipped"

                        vul_id = uuid.uuid4()

                        save_all = InspecScanResultsDb(
                            scan_id=scan_id,
                            project_id=project_id,
                            vul_col=vul_col,
                            vuln_id=vul_id,
                            controls_id=controls_id,
                            controls_title=controls_title,
                            controls_desc=controls_desc,
                            controls_descriptions=controls_descriptions,
                            controls_impact=controls_impact,
                            controls_refs=controls_refs,
                            controls_tags_severity=controls_tags_severity,
                            controls_tags_cis_id=controls_tags_cis_id,
                            controls_tags_cis_control=controls_tags_cis_control,
                            controls_tags_cis_level=controls_tags_cis_level,
                            controls_tags_audit=controls_tags_audit,
                            controls_tags_fix=controls_tags_fix,
                            controls_code=controls_code,
                            controls_source_location=controls_source_location,
                            controls_results_status=status,
                            controls_results_code_desc=controls_results_code_desc,
                            controls_results_run_time=controls_results_run_time,
                            controls_results_start_time=controls_results_start_time,
                            controls_results_message=controls_results_message,
                            organization=organization,
                        )
                        save_all.save()

            all_inspec_data = InspecScanResultsDb.objects.filter(
                scan_id=scan_id, organization=organization
            )

            total_vul = len(all_inspec_data)
            inspec_failed = len(
                all_inspec_data.filter(
                    controls_results_status="Failed",
                    organization=organization,
                )
            )
            inspec_passed = len(
                all_inspec_data.filter(
                    controls_results_status="Passed",
                    organization=organization,
                )
            )
            inspec_skipped = len(
                all_inspec_data.filter(
                    controls_results_status="Skipped",
                    organization=organization,
                )
            )
            total_duplicate = len(
                all_inspec_data.filter(
                    vuln_duplicate="Yes", organization=organization
                )
            )

            InspecScanDb.objects.filter(
                scan_id=scan_id, organization=organization
            ).update(
                total_vuln=total_vul,
                inspec_failed=inspec_failed,
                inspec_passed=inspec_passed,
                inspec_skipped=inspec_skipped,
                total_dup=total_duplicate,
                organization=organization,
            )
            subject = "Archery Tool Scan Status - Inspec Report Uploaded"
            message = (
                "Inspec Scanner has completed the scan "
                "  %s <br> Total: %s <br>Failed: %s <br>"
                "failed: %s <br>Skipped %s"
                % (scan_id, total_vul, inspec_failed, inspec_failed, inspec_skipped)
            )

            email_sch_notify(subject=subject, message=message)


parser_header_dict = {
    "inspec_scan": {
        "displayName": "Inspec Scanner",
        "dbtype": "InspecScan",
        "type": "JSON",
        "parserFunction": inspec_report_json,
        "icon": "/static/tools/inspec.png",
    }
}

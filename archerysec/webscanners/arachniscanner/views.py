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

from __future__ import unicode_literals

import hashlib
import json
import threading
import time
import uuid
from datetime import datetime

import defusedxml.ElementTree as ET
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from notifications.signals import notify
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import PyArachniapi
from archerysettings.models import ArachniSettingsDb, SettingsDb
from jiraticketing.models import jirasetting
from projects.models import ProjectDb
from scanners.scanner_parser.web_scanner import arachni_xml_parser
from user_management import permissions
from webscanners.arachniscanner.serializers import (ArachniScansSerializer,
                                                    ArachniSettingsSerializer)
from webscanners.models import WebScanResultsDb, WebScansDb
from webscanners.resources import ArachniResource

scan_run_id = ""
scan_status = ""


def launch_arachni_scan(target, project_id, rescan_id, rescan, scan_id, user):
    global scan_run_id, scan_status
    arachni_hosts = None
    arachni_ports = None
    arachni_user = ""
    arachni_pass = ""
    all_arachni = ArachniSettingsDb.objects.filter()
    for arachni in all_arachni:
        arachni_hosts = arachni.arachni_url
        arachni_ports = arachni.arachni_port
        arachni_user = arachni.arachni_user
        arachni_pass = arachni.arachni_pass

    arachni = PyArachniapi.arachniAPI(
        arachni_hosts, arachni_ports, arachni_user, arachni_pass
    )
    check = [
        "xss_event",
        "xss",
        "xss_script_context",
        "xss_tag",
        "xss_path",
        "xss_dom_script_context",
        "xss_dom",
        "sql_injection",
        "sql_injection_differential",
        "sql_injection_timing",
        "no_sql_injection",
        "no_sql_injection_differential",
        "code_injection",
        "code_injection_timing",
        "ldap_injection",
        "path_traversal",
        "file_inclusion",
        "response_splitting",
        "os_cmd_injection",
        "os_cmd_injection_timing",
        "rfi",
        "unvalidated_redirect",
        "unvalidated_redirect_dom",
        "xpath_injection",
        "xxe",
        "source_code_disclosure",
        "allowed_methods",
        "backup_files",
        "backup_directories",
        "common_admin_interfaces",
        "common_directories",
        "common_files",
        "http_put",
        "webdav",
        "xst",
        "credit_card",
        "cvs_svn_users",
        "private_ip",
        "backdoors",
        "htaccess_limit",
        "interesting_responses",
        "html_objects",
        "emails",
        "ssn",
        "directory_listing",
        "mixed_resource",
        "insecure_cookies",
        "http_only_cookies",
        "password_autocomplete",
        "origin_spoof_access_restriction_bypass",
        "form_upload",
        "localstart_asp",
        "cookie_set_for_parent_domain",
        "hsts",
        "x_frame_options",
        "insecure_cors_policy",
        "insecure_cross_domain_policy_access",
        "insecure_cross_domain_policy_headers",
        "insecure_client_access_policy",
        "csrf",
        "common_files",
        "directory_listing",
    ]

    data = {"url": target, "checks": check, "audit": {}}
    d = json.dumps(data)

    scan_launch = arachni.scan_launch(d)
    time.sleep(3)

    try:
        scan_data = scan_launch.data

        for key, value in scan_data.items():
            if key == "id":
                scan_run_id = value
        notify.send(
            user, recipient=user, verb="Arachni Scan Started on URL %s" % target
        )
    except Exception:
        notify.send(user, recipient=user, verb="Arachni Connection Not found")
        print("Arachni Connection Not found")
        return

    date_time = datetime.now()

    try:
        save_all_scan = WebScansDb(
            project_id=project_id,
            scan_url=target,
            scan_id=scan_id,
            date_time=date_time,
            scanner="Arachni",
        )

        save_all_scan.save()

    except Exception as e:
        print(e)

    scan_data = scan_launch.data

    for key, value in scan_data.items():
        if key == "id":
            scan_run_id = value

    scan_sum = arachni.scan_summary(id=scan_run_id).data
    for key, value in scan_sum.items():
        if key == "status":
            scan_status = value
    while scan_status != "done":
        status = "0"
        if (
            scan_sum["statistics"]["browser_cluster"]["queued_job_count"]
            and scan_sum["statistics"]["browser_cluster"]["total_job_time"]
        ):
            status = (
                100
                - scan_sum["statistics"]["browser_cluster"]["queued_job_count"]
                * 100
                / scan_sum["statistics"]["browser_cluster"]["total_job_time"]
            )
        WebScansDb.objects.filter(scan_id=scan_id, scanner="Arachni").update(
            scan_status=int(status)
        )
        scan_sum = arachni.scan_summary(id=scan_run_id).data
        for key, value in scan_sum.items():
            if key == "status":
                scan_status = value
        time.sleep(3)
    if scan_status == "done":
        xml_report = arachni.scan_xml_report(id=scan_run_id).data
        root_xml = ET.fromstring(xml_report)
        arachni_xml_parser.xml_parser(
            project_id=project_id,
            scan_id=scan_id,
            root=root_xml,
            target_url=target,
        )
        WebScansDb.objects.filter(scan_id=scan_id, scanner="Arachni").update(
            scan_status="100"
        )
        print("Data uploaded !!!!")

    notify.send(user, recipient=user, verb="Arachni Scan Completed on URL %s" % target)


class ArachniScan(APIView):
    permission_classes = (IsAuthenticated, permissions.IsAnalyst)

    def get(self, request):
        return render(request, "webscanners/webscanner.html")

    def post(self, request):
        scan_id = None
        project_uu_id = None
        target_url = None

        user = request.user
        if request.path[:4] == "/api":
            serializer = ArachniScansSerializer(data=request.data)
            if serializer.is_valid():
                target_url = request.data.get(
                    "url",
                )
                project_uu_id = request.data.get(
                    "project_id",
                )
        else:
            target_url = request.POST.get("scan_url")
            project_uu_id = request.POST.get("project_id")
        project_id = (
            ProjectDb.objects.filter(uu_id=project_uu_id).values("id").get()["id"]
        )
        rescan_id = None
        rescan = "No"
        target_item = str(target_url)
        value = target_item.replace(" ", "")
        target__split = value.split(",")
        split_length = target__split.__len__()
        for i in range(0, split_length):
            target = target__split.__getitem__(i)
            scan_id = uuid.uuid4()
            thread = threading.Thread(
                target=launch_arachni_scan,
                args=(target, project_id, rescan_id, rescan, scan_id, user),
            )
            thread.daemon = True
            thread.start()

            if request.path[:4] == "/api":
                return Response({"scan_id": scan_id})

        if request.path[:4] == "/api":
            return Response({"scan_id": scan_id})
        else:
            return render(request, "webscanners/scans/list_scans.html")


class ArachniSetting(APIView):
    permission_classes = (IsAuthenticated, permissions.IsAnalyst)

    def get(self, request):
        arachni_hosts = None
        arachni_ports = None
        arachni_user = None
        arachni_pass = None

        all_arachni = ArachniSettingsDb.objects.filter()
        for arachni in all_arachni:
            # global arachni_api_key, arachni_hosts, arachni_ports
            arachni_hosts = arachni.arachni_url
            arachni_ports = arachni.arachni_port
            arachni_user = arachni.arachni_user
            arachni_pass = arachni.arachni_pass

        if request.path[:4] == "/api":
            return Response(
                {
                    "arachni_host": arachni_hosts,
                    "arachni_port": arachni_ports,
                    "arachni_user": arachni_user,
                    "arachni_pass": arachni_pass,
                }
            )
        else:
            return render(
                request,
                "webscanners/arachniscanner/arachni_settings_form.html",
                {
                    "arachni_host": arachni_hosts,
                    "arachni_port": arachni_ports,
                    "arachni_user": arachni_user,
                    "arachni_pass": arachni_pass,
                },
            )


class ArachniSettingUpdate(APIView):
    permission_classes = (IsAuthenticated, permissions.IsAnalyst)

    def get(self, request):
        return render(request, "webscanners/arachniscanner/arachni_settings_form.html")

    def post(self, request):
        setting_id = uuid.uuid4()
        arachnihost = None
        port = None
        user = None
        password = None

        if request.path[:4] == "/api":
            serializer = ArachniSettingsSerializer(data=request.data)
            if serializer.is_valid():
                arachnihost = request.data.get(
                    "arachni_hosts",
                )
                port = request.data.get(
                    "arachni_ports",
                )
                user = request.data.get(
                    "arachni_user",
                )
                password = request.data.get(
                    "arachni_pass",
                )
            else:
                return Response({"message": "Not Valid Data"})

        else:
            arachnihost = request.POST.get(
                "arachnihost",
            )
            port = request.POST.get(
                "arachniport",
            )
            user = request.POST.get(
                "arachniuser",
            )
            password = request.POST.get(
                "arachnipass",
            )

        setting_dat = SettingsDb(
            setting_id=setting_id,
            setting_scanner="Arachni",
        )
        setting_dat.save()

        save_data = ArachniSettingsDb(
            arachni_url=arachnihost,
            arachni_port=port,
            arachni_user=user,
            arachni_pass=password,
            setting_id=setting_id,
        )
        save_data.save()

        arachni = PyArachniapi.arachniAPI(arachnihost, port, user, password)

        check = []
        data = {"url": "https://archerysec.com", "checks": check, "audit": {}}
        d = json.dumps(data)

        scan_launch = arachni.scan_launch(d)
        time.sleep(3)

        try:
            scan_data = scan_launch.data

            for key, value in scan_data.items():
                if key == "id":
                    scan_run_id = value
            arachni_info = True
            SettingsDb.objects.filter(setting_id=setting_id).update(
                setting_status=arachni_info
            )
        except Exception:
            arachni_info = False
            SettingsDb.objects.filter(setting_id=setting_id).update(
                setting_status=arachni_info
            )

        if request.path[:4] == "/api":
            return Response({"message": "Arachani scanner updated!!!"})
        else:
            return HttpResponseRedirect(reverse("archerysettings:settings"))


def export(request):
    """
    :param request:
    :return:
    """
    if request.method == "POST":
        scan_id = request.POST.get("scan_id")
        report_type = request.POST.get("type")

        scan_item = str(scan_id)
        value = scan_item.replace(" ", "")
        value_split = value.split(",")

        zap_resource = ArachniResource()
        queryset = WebScanResultsDb.objects.filter(
            scan_id__in=value_split, scanner="Arachni"
        )
        dataset = zap_resource.export(queryset)
        if report_type == "csv":
            response = HttpResponse(dataset.csv, content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="%s.csv"' % "arachni_results"
            )
            return response
        if report_type == "json":
            response = HttpResponse(dataset.json, content_type="application/json")
            response["Content-Disposition"] = (
                'attachment; filename="%s.json"' % "arachni_results"
            )
            return response
        if report_type == "yaml":
            response = HttpResponse(dataset.yaml, content_type="application/x-yaml")
            response["Content-Disposition"] = (
                'attachment; filename="%s.yaml"' % "arachni_results"
            )
            return response

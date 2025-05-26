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

import csv
import io
import json
import os
import uuid
from datetime import datetime

import defusedxml.ElementTree as ET
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from lxml import etree
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.views import APIView

from cloudscanners.models import CloudScansDb
from compliance.models import DockleScanDb, InspecScanDb
from networkscanners.models import NetworkScanDb
from projects.models import ProjectDb
from scanners.scanner_parser import scanner_parser
from scanners.scanner_parser.network_scanner import OpenVas_Parser
from staticscanners.models import StaticScansDb
from tools.models import NiktoResultDb
from user_management import permissions
from webscanners.models import WebScansDb


class Upload(APIView):
    parser_classes = (MultiPartParser,)
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "report_upload/upload.html"

    permission_classes = (IsAuthenticated, permissions.IsAnalyst)

    def check_file_ext(self, file):
        split_tup = os.path.splitext(file)
        file_extension = split_tup[1]
        return file_extension

    def get(self, request):
        all_project = ProjectDb.objects.filter(organization=request.user.organization)

        return render(
            request, "report_upload/upload.html", {"all_project": all_project}
        )

    def post(self, request):
        all_project = ProjectDb.objects.filter(organization=request.user.organization)
        project_uu_id = request.POST.get("project_id")
        project_id = (
            ProjectDb.objects.filter(
                uu_id=project_uu_id, organization=request.user.organization
            )
            .values("id")
            .get()["id"]
        )
        scanner = request.POST.get("scanner")
        file = request.FILES["file"]
        target = request.POST.get("target")
        scan_id = uuid.uuid4()
        scan_status = "100"

        try:
            parser_dict = scanner_parser.parser_function_dict[scanner]
            filetype = parser_dict["type"]
            fileext = ""
            returnpage = ""

            # Regular file formats (XML/JSON/CSV)
            if filetype == "XML" or filetype == "LXML":
                fileext = ".xml"
            elif filetype == "JSON":
                fileext = ".json"
            elif filetype == "CSV":
                fileext = ".csv"
            # Custom file formats
            elif filetype == "Nessus":
                fileext = ".nessus"
            elif filetype == "JS":
                fileext = ".js"
            elif filetype == "HTML":
                fileext = ".html"
            # Check file format
            if self.check_file_ext(str(file)) != fileext or fileext == "":
                error_mess = (
                    parser_dict["displayName"] + " Only " + filetype + " file support"
                )
                messages.error(request, error_mess)
                return HttpResponseRedirect(reverse("report_upload:upload"))

            # Create datetime for timestamp
            date_time = datetime.now()
            # Put the data in memory
            if filetype == "XML" or filetype == "Nessus":
                tree = ET.parse(file)
                root_xml = tree.getroot()
                en_root_xml = ET.tostring(root_xml, encoding="utf8").decode(
                    "ascii", "ignore"
                )
                data = ET.fromstring(en_root_xml)
            elif filetype == "LXML":
                tree = etree.parse(file)
                data = tree.getroot()
            elif filetype == "JSON":
                jsonContents = file.read()
                data = json.loads(jsonContents)
            elif filetype == "CSV":
                file_data = file.read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(file_data))
                data = [line for line in reader]
            elif filetype == "HTML":
                data = file.read()
            # Custom data loader
            elif filetype == "JS":
                json_payload = file.readlines()
                json_payload.pop(0)
                for d in json_payload:
                    json_file = json.loads(d)
                    data = json_file

            db_type = parser_dict["dbtype"]
            need_to_store = True
            # Store to database - regular types
            if "dbname" in parser_dict:
                db_name = parser_dict["dbname"]
                if db_type == "WebScans":
                    returnpage = "webscanners:list_scans"
                    scan_dump = WebScansDb(
                        scan_url=target,
                        scan_id=scan_id,
                        date_time=date_time,
                        project_id=project_id,
                        scan_status=scan_status,
                        rescan="No",
                        scanner=db_name,
                        organization=request.user.organization,
                    )
                elif db_type == "StaticScans":
                    returnpage = "staticscanners:list_scans"
                    scan_dump = StaticScansDb(
                        project_name=target,
                        scan_id=scan_id,
                        date_time=date_time,
                        project_id=project_id,
                        scan_status=scan_status,
                        scanner=db_name,
                        organization=request.user.organization,
                    )
                elif db_type == "NetworkScan":
                    returnpage = "networkscanners:list_scans"
                    # OpenVAS special case
                    if scanner == "openvas":
                        need_to_store = False
                        hosts = OpenVas_Parser.get_hosts(root_xml)
                        for host in hosts:
                            scan_dump = NetworkScanDb(
                                ip=host,
                                scan_id=scan_id,
                                date_time=date_time,
                                project_id=project_id,
                                scan_status=scan_status,
                                scanner=db_name,
                                organization=request.user.organization,
                            )
                            scan_dump.save()
                    # Regular network scan case
                    else:
                        host = parser_dict["getHostFunction"](data)
                        scan_dump = NetworkScanDb(
                            ip=host,
                            scan_id=scan_id,
                            date_time=date_time,
                            project_id=project_id,
                            scan_status=scan_status,
                            scanner=db_name,
                            organization=request.user.organization,
                        )
                elif db_type == "CloudScans":
                    returnpage = "cloudscanners:list_scans"
                    scan_dump = CloudScansDb(
                        scan_id=scan_id,
                        date_time=date_time,
                        project_id=project_id,
                        scan_status=scan_status,
                        rescan="No",
                        scanner=db_name,
                        organization=request.user.organization,
                    )
            # Store to database - custom types
            elif db_type == "NiktoResult":
                returnpage = "tools:nikto"
                scan_dump = NiktoResultDb(
                    date_time=date_time,
                    scan_url=target,
                    scan_id=scan_id,
                    project_id=project_id,
                    organization=request.user.organization,
                )
            elif db_type == "InspecScan":
                returnpage = "inspec:inspec_list"
                scan_dump = InspecScanDb(
                    scan_id=scan_id,
                    date_time=date_time,
                    project_id=project_id,
                    scan_status=scan_status,
                    organization=request.user.organization,
                )
            elif db_type == "DockleScan":
                returnpage = "dockle:dockle_list"
                scan_dump = DockleScanDb(
                    scan_id=scan_id,
                    date_time=date_time,
                    project_id=project_id,
                    scan_status=scan_status,
                    organization=request.user.organization,
                )
            elif db_type == "Nessus":
                need_to_store = False
                returnpage = "networkscanners:list_scans"
                # Nessus does not store before the parser
            # Store the dump (except for no need to store cases)
            if need_to_store is True:
                scan_dump.save()

            # Call the parser
            parserFunc = parser_dict["parserFunction"]
            parserFunc(data, project_id, scan_id, request)

            # Success !
            messages.success(request, "File Uploaded")
            return HttpResponseRedirect(reverse(returnpage))

        except Exception as e:
            print(e)
            messages.error(request, "File Not Supported")
            return render(
                request, "report_upload/upload.html", {"all_project": all_project}
            )

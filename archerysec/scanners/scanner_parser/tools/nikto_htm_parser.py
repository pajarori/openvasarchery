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

from bs4 import BeautifulSoup
from archeryapi.models import OrgAPIKey

from tools.models import NiktoVulnDb


def nikto_html_parser(data, project_id, scan_id, request):
    discription = "None"
    targetip = "None"
    hostname = "None"
    port = "None"
    uri = "None"
    httpmethod = "None"
    testlinks = "None"
    osvdb = "None"
    soup = BeautifulSoup(data, "html.parser")

    api_key = request.META.get("HTTP_X_API_KEY")
    key_object = OrgAPIKey.objects.filter(api_key=api_key).first()
    if str(request.user) == 'AnonymousUser':
        organization = key_object.organization
    else:
        organization = request.user.organization

    for link in soup.find_all(class_="dataTable"):
        # print "------------------------"
        table_rows = link.find_all("tr")
        for tr in table_rows:
            for tt in tr.find_all(class_="column-head"):
                if tt.text == "Description":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "Description:", ttt.text
                    discription = ttt.text
                if tt.text == "Target IP":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "Target IP", ttt.text
                    targetip = ttt.test
                if tt.text == "Target hostname":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "Target hostname", ttt.text
                    hostname = ttt.text
                if tt.text == "Target Port":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "Target Port", ttt.text
                    port = ttt.text

                if tt.text == "URI":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "URI:", ttt.text
                    uri = ttt.text
                if tt.text == "HTTP Method":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "HTTP Method:", ttt.text
                    httpmethod = ttt.text
                if tt.text == "Test Links":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "Test Links:", ttt.text
                    testlinks = ttt.text
                if tt.text == "OSVDB Entries":
                    for ttt in tr.find_all("td"):
                        for tttt in ttt.find_all("b"):
                            del tttt
                    # print "OSVDB Entries:", ttt.text
                    osvdb = ttt.text

        vuln_id = uuid.uuid4()

        dup_data = discription + hostname
        duplicate_hash = hashlib.sha256(dup_data.encode("utf-8")).hexdigest()

        match_dup = (
            NiktoVulnDb.objects.filter(
                dup_hash=duplicate_hash, organization=organization
            )
            .values("dup_hash")
            .distinct()
        )
        lenth_match = len(match_dup)

        if lenth_match == 1:
            duplicate_vuln = "Yes"
        elif lenth_match == 0:
            duplicate_vuln = "No"
        else:
            duplicate_vuln = "None"

        false_p = NiktoVulnDb.objects.filter(
            false_positive_hash=duplicate_hash, organization=organization
        )
        fp_lenth_match = len(false_p)

        global false_positive
        if fp_lenth_match == 1:
            false_positive = "Yes"
        elif lenth_match == 0:
            false_positive = "No"
        else:
            false_positive = "No"

        dump_data = NiktoVulnDb(
            vuln_id=vuln_id,
            scan_id=scan_id,
            project_id=project_id,
            discription=discription,
            targetip=targetip,
            hostname=hostname,
            port=port,
            uri=uri,
            httpmethod=httpmethod,
            testlinks=testlinks,
            osvdb=osvdb,
            false_positive=false_positive,
            dup_hash=duplicate_hash,
            vuln_duplicate=duplicate_vuln,
            vuln_status="Open",
            organization=organization,
        )
        dump_data.save()


parser_header_dict = {
    "nikto": {
        "displayName": "Nikto",
        "dbtype": "NiktoResult",
        "type": "XML",
        "parserFunction": nikto_html_parser,
    }
}

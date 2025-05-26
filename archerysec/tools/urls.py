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

from django.urls import include, path

from tools import views

app_name = "tools"

urlpatterns = [
    path("sslscan/", views.SslScanList.as_view(), name="sslscan"),
    path("sslscanlaunch/", views.SslScanLaunch.as_view(), name="sslscanlaunch"),
    path("sslscan_result/", views.SslScanResult.as_view(), name="sslscan_result"),
    path("sslcan_del/", views.SslScanDelete.as_view(), name="sslcan_del"),
    # Nikto requests
    path("nikto/", views.NiktoScanList.as_view(), name="nikto"),
    path("niktolaunch/", views.NiktoScanLaunch.as_view(), name="niktolaunch"),
    path("nikto_result/", views.NiktoScanResult.as_view(), name="nikto_result"),
    path("nikto_scan_del/", views.NiktoScanDelete.as_view(), name="nikto_scan_del"),
    path("nikto_result_vul/", views.NiktoResultVuln.as_view(), name="nikto_result_vul"),
    path("nikto_vuln_del/", views.NiktoVulnDelete.as_view(), name="nikto_vuln_del"),
    # nmap requests
    path("nmap_scan/", views.NmapScan.as_view(), name="nmap_scan"),
    path("nmap/", views.Nmap.as_view(), name="nmap"),
    path("nmap_result/", views.NmapResult.as_view(), name="nmap_result"),
    path("nmap_scan_del/", views.NmapScanDelete.as_view(), name="nmap_scan_del"),
    # Nmap_Vulners
    path("nmap_vulners_scan/", views.nmap_vulners_scan, name="nmap_scan"),
    path("nmap_vulners/", views.nmap_vulners, name="nmap_vulners"),
    path("nmap_vulners_port_list/", views.nmap_vulners_port, name="nmap_vulners_port"),
]

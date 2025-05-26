from django.conf import settings
from django.core.mail import send_mail

from archerysettings.models import EmailDb


def email_sch_notify(subject, message):
    to_mail = ""
    all_email = EmailDb.objects.all()
    for email in all_email:
        to_mail = email.recipient_list

    print(to_mail)
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [to_mail]
    try:
        send_mail(subject, message, email_from, recipient_list)
        return True
    except Exception as e:
        print(e)
        return False

from globaleaks.utils import log
import smtplib
import string

I_WANT_TO_BE_SPAMMED = False

# would be remove at the end
def do_not_email(subject, body, receiver_addr):
    from globaleaks.utils import gltime

    with file("/tmp/do_not_email_please", 'a+') as f:
        f.write('\r\nTime: %s' % gltime.utcPrettyDateNow())
        f.write('\r\nDest: %s' % receiver_addr)
        f.write('\r\nSubject: %s\r\n' % subject)
        f.write(body)
        f.write("\r\n---\r\n")

def GLBMailService(eventdate, infotext, receiver_addr):
    """
    This is a temporary email supports not yet pluginized
    """
    username='globaleaksnode1@gmail.com'
    password='Antani1234'
    serverport='smtp.gmail.com:587'

    subject = "Email notification for %s" % (receiver_addr.split('@')[0])

    text = "In %s an info for you: [%s]" % (eventdate, infotext)

    # XXX just for avoid getting spammed when testing GLB :P
    if not I_WANT_TO_BE_SPAMMED:
        do_not_email(subject, text, receiver_addr)
        return True

    body = string.join(("From: GLBackend postino <%s>" % username,
                        "To: Estimeed Receiver <%s>" % receiver_addr,
                        "Subject: %s" % subject, text), "\r\n")

    server = smtplib.SMTP(serverport)
    server.starttls()
    server.login(username, password)

    try:
        server.sendmail(username, [ receiver_addr ], body)
        log.debug("Success in email %s " % tip_gus)
        server.quit()
        retval = True
    except smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused:
        # remind, other error can be handled http://docs.python.org/2/library/smtplib.html
        log.err("[E] error in sending the email to %s %s (%s)" % (receiver_addr, infotext, subject))
        retval = False

    return retval


# class email(Notification)
# 
# plugin_type = "notification"
# plugin_name = "Twitter PM notification"
# plugin_description = $(localized pointer)
# 
# def get_admin_opt():
#   return pluginAdminDict

#
# def set_admin_opt(pluginAdminDict):
#
# def get_receiver_opt(pluginDataDict):

# def set_receiver_opt():
#   return pluginDataDict
#
# def do_notify():
#
# def get_log():

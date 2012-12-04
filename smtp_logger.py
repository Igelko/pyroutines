# -*- coding: utf-8 -*-

import logging
from logging.handlers import BufferingHandler
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.header import Header


#Yes, i'm evil.
logging.basicConfig(encoding='UTF-8')


class BufferedSMTPHandler(BufferingHandler):
    """
    Collects logs and sends to e-mail on the flush. Dumb and not thread-safe.
    """

    def __init__(self, level, capacity, host, port,
                    fromaddr, toaddrs, user=None, passwd=None,
                    subject='logs', encoding='utf-8'):
        BufferingHandler.__init__(self, capacity)
        self.setLevel(level)
        self.host = host
        self.port = port
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs if isinstance(toaddrs, (list, tuple)) else [toaddrs]
        self.user = user
        self.passwd = passwd
        self.subject = Header(subject)
        self.encoding = encoding

    def flush(self):
        try:
            if self.buffer != []:
                # Make message.
                message = u"\n".join(map(lambda r: self.format(r), self.buffer))
                msg = MIMEText(message, "plain", self.encoding)
                msg["Subject"] = self.subject
                #sends mail.
                smtp = SMTP(self.host, self.port)
                #smtp.set_debuglevel(True)
                if self.user and self.passwd:
                    smtp.login(self.user, self.passwd)
                smtp.sendmail(self.fromaddr, self.toaddrs, msg.as_string())
                smtp.quit()
                self.buffer = []
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            logging.error(e.message.encode("utf-8"))
            raise


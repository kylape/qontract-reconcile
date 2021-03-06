import smtplib

import utils.secret_reader as secret_reader

from utils.config import get_config

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

_client = None
_username = None
_mail_address = None


def init(host, port, username, password):
    global _client

    if _client is None:
        s = smtplib.SMTP(
            host=host,
            port=str(port)
        )
        s.send
        s.starttls()
        s.login(username, password)
        _client = s

    return _client


def teardown():
    global _client

    _client.quit()


def init_from_config(settings):
    global _username
    global _mail_address

    config = get_config()
    smtp_secret_path = config['smtp']['secret_path']
    smtp_config = get_smtp_config(smtp_secret_path, settings)
    host = smtp_config['server']
    port = smtp_config['port']
    _username = smtp_config['username']
    password = smtp_config['password']
    _mail_address = config['smtp']['mail_address']

    return init(host, port, _username, password)


def get_smtp_config(path, settings):
    config = {}

    required_keys = ('password', 'port', 'require_tls', 'server', 'username')
    data = secret_reader.read_all({'path': path}, settings=settings)

    try:
        for k in required_keys:
            config[k] = data[k]
    except KeyError as e:
        raise Exception("Missing expected SMTP config key in vault secret: {}"
                        .format(e))

    return config


def send_mail(names, subject, body, settings=None):
    global _client
    global _username
    global _mail_address

    if _client is None:
        init_from_config(settings)

    msg = MIMEMultipart()
    from_name = str(Header('App SRE team automation', 'utf-8'))
    msg['From'] = formataddr((from_name, _username))
    to = set()
    for name in names:
        if '@' in name:
            to.add(name)
        else:
            to.add(f"{name}@{_mail_address}")
    msg['To'] = ', '.join(to)
    msg['Subject'] = subject

    # add in the message body
    msg.attach(MIMEText(body, 'plain'))

    # send the message via the server set up earlier.
    _client.sendmail(_username, to, msg.as_string())


def send_mails(mails, settings=None):
    global _client

    init_from_config(settings)
    try:
        for name, subject, body in mails:
            send_mail([name], subject, body)
    finally:
        teardown()


def get_recepient(org_username, settings):
    global _client
    global _mail_address

    if _client is None:
        init_from_config(settings)

    return f"{org_username}@{_mail_address}"

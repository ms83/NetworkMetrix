import os
import sys
import copy
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError


class Config(object):
    """ Class for handling config file """

    def __init__(self, filename=os.path.join('..', 'config.xml')):
        self.filename = filename
        self.client = {}

        try:
            self._read_config_file(filename)
        except (IOError, ExpatError, IndexError), e:
            sys.stderr.write('ERROR in `{}`. Invalid config file. {}\r\n'.format(self.filename, e))
            sys.exit(1)

    def _parse_int_value(self, parent, name):
        try:
            return int(self._parse_str_value(parent, name))
        except ValueError:
            sys.stderr.write('ERROR in `{}`. Invalid value for `{}`\r\n'.format(self.filename, name))
            sys.exit(2)

    def _parse_str_value(self, parent, name):
        try:
            return parent.getElementsByTagName(name)[0].firstChild.data
        except (AttributeError, IndexError):
            sys.stderr.write('ERROR in `{}`. Invalid value for `{}`\r\n'.format(self.filename, name))
            sys.exit(3)

    def _parse_alert(self, node):
        conditions = ('gt', 'lt')
        if node.getAttribute('condition') not in ('gt', 'lt'):
            sys.stderr.write('ERROR in `{}`. Invalid value for `condition`. Choose one of {}\r\n'.\
                             format(self.filename, conditions))
            sys.exit(4)

        try:
            return {
                'limit': int(node.getAttribute('limit')),
                'condition': node.getAttribute('condition')
            }
        except ValueError, e:
            sys.stderr.write('ERROR in `{}`. Invalid value for `limit`. {}\r\n'.format(self.filename, e))
            sys.exit(5)

    def _read_config_file(self, filename):
        dom = parse(filename)
        config_tag = dom.getElementsByTagName('config')[0]

        log_levels = ('ERROR', 'INFO', 'DEBUG')
        self.log_level = self._parse_str_value(config_tag, 'loglevel')
        if self.log_level not in log_levels:
            sys.stderr.write('ERROR in `{}`. Invalid value for `loglevel`. Choose one of {}\r\n'.\
                             format(self.filename, log_levels))
            sys.exit(6)

        self.concurrency = self._parse_int_value(config_tag, 'concurrency')
        self.database = self._parse_str_value(config_tag, 'database')
        self.script = self._parse_str_value(config_tag, 'script')

        smtp = dom.getElementsByTagName('smtp')[0]
        self.smtp_returnpath = self._parse_str_value(smtp, 'returnpath')
        self.smtp_envelope = self._parse_str_value(smtp, 'envelope')
        self.smtp_hostname = self._parse_str_value(smtp, 'hostname')
        self.smtp_port = self._parse_int_value(smtp, 'port')

        default_tag = config_tag.getElementsByTagName('default')[0]
        default = {}
        for tag in ('target', 'mail', 'python', 'username', 'password'):
            default[tag] = self._parse_str_value(default_tag, tag)

        default['port'] = self._parse_int_value(default_tag, 'port')

        default_alerts = {}
        for alert in default_tag.getElementsByTagName('alert'):
            t = alert.getAttribute('type')
            default_alerts[t] = self._parse_alert(alert)

        for client in config_tag.getElementsByTagName('client'):
            ip = client.getAttribute('ip')

            # Override by default values if specific values not set
            for tag in ('target', 'mail', 'python', 'username', 'password', 'port'):
                if not client.hasAttribute(tag):
                    client.setAttribute(tag, default[tag])

            # Assign all attributes
            self.client[ip] = client.attributes.items()

            # Get default alerts and override by custom client alerts
            client_alerts = copy.deepcopy(default_alerts)
            for alert in client.getElementsByTagName('alert'):
                t = alert.getAttribute('type')
                client_alerts[t] = self._parse_alert(alert)

            self.client[ip].append( ('alert', client_alerts) )

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'''
Clients ({}):\t{}
Concurrency:\t{}
Script:\t\t{}
Database:\t{}
Return path:\t{}
Envelope:\t{}
SMTP host:\t{}
SMTP port:\t{}
Log level:\t{}
'''.format(len(self.client), self.client.keys(),
               self.concurrency,
               self.script,
               self.database,
               self.smtp_returnpath,
               self.smtp_envelope,
               self.smtp_hostname,
               self.smtp_port,
               self.log_level)


# Configuration singleton
cf = Config()

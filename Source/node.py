import os
import json
import socket
import smtplib
import logging
import paramiko
from paramiko.ssh_exception import (
    AuthenticationException, 
    SSHException, 
    NoValidConnectionsError
)
from client import decrypt
from config import cf
from database import DB


logger = logging.getLogger('networkmetrix')

class Node(object):
    def __init__(self, client):
        self.alert = {}
        for k, v in client:
            setattr(self, k, v)

        for field in ('ip', 'password', 'username', 'password', 'target', 'python'):
            assert getattr(self, field) 

    def upload(self):
        try:
            t = paramiko.Transport((self.ip, int(self.port)))
            t.connect(username=self.username, password=self.password)
        except SSHException, e:
            logger.error('upload[%s] Script not uploaded. %s', self.ip, e)
            return

        try:
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.put(cf.script, self._client_remote_loc)
            logger.info('upload[%s] SUCCESS! Script uploaded to `%s`', self.ip, self._client_remote_loc)
        except AuthenticationException, e:
            logger.error('upload[%s] Script not uploaded. %s', self.ip, e)
        finally:
            sftp.close()
            t.close()

    def execute(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
            client.connect(self.ip, username=self.username, password=self.password)
        except (SSHException, NoValidConnectionsError), e:
            logger.error('execute[%s] Script not executed. %s', self.ip, e)
            return

        stdin, stdout, stderr = client.exec_command('{} {}'.format(self.python, self._client_remote_loc))

        # Convert traceback to one line
        stderr_str = ' '.join(stderr.read().strip().split('\n'))
        stdout_str = stdout.read().strip()
        client.close()

        if not stdout_str:
            logger.error('execute[%s] Empty respone from `%s`. %s', self.ip, self._client_remote_loc, stderr_str)
            return

        logger.info('execute[%s] SUCCESS! Script `%s` executed', self.ip, self._client_remote_loc)

        metrics = json.loads(decrypt(stdout_str))

        # Store metrics in relational database
        # New database connection will be opened to prevent from 
        # database being bottleneck. All rows will be inserted
        # on one connection.
        with DB() as conn:
            for metric_key, metric_value in metrics.iteritems():
                conn.insert_metric(self.ip, metric_key, metric_value)
                logger.debug('execute[%s] Metric `%s`->`%s` saved', self.ip, metric_key, metric_value)

        # Send alert if required
        for metric_key, metric_value in metrics.iteritems():
            self._check_alert(metric_key, metric_value)

    def _check_alert(self, metric_key, metric_value):
        alert = self.alert.get(metric_key)
        if not alert:
            return

        if alert['condition'] == 'gt' and int(metric_value) > alert['limit']:
            self._send_alert(alert, metric_key, metric_value)

        if alert['condition'] == 'lt' and int(metric_value) < alert['limit']:
            self._send_alert(alert, metric_key, metric_value)

    def _send_alert(self, alert, metric_key, metric_value):
        C_ = {'gt': '>', 'lt': '<'}
        subject = 'ALERT [{}] {} is {}{}{}'.format(self.ip,
                                                  metric_key,
                                                  metric_value,  
                                                  C_[alert['condition']],
                                                  alert['limit'])

        body = '{} on {} is {} which is {} than limit {}'.format(metric_key, 
                                                            self.ip, 
                                                            metric_value,  
                                                            C_[alert['condition']],
                                                            alert['limit'])
                                                            
        msg = '''From: {} <{}>\r\nTo: {}\r\nSubject: {}\r\n\r\n{}'''.format(
                                                                    cf.smtp_envelope,
                                                                    cf.smtp_returnpath,
                                                                    self.mail,
                                                                    subject,
                                                                    body)
        try:
            server = smtplib.SMTP(cf.smtp_hostname, cf.smtp_port)
        except socket.error, e:
            logger.error('execute[%s] Mail `%s` not sent to `%s`. %s', self.ip, subject, self.mail, e)
            return

        try:
            server.sendmail(cf.smtp_returnpath, [self.mail], msg)
            logger.info('execute[%s] Mail `%s` sent to `%s`', self.ip, subject, self.mail)
        except smtplib.SMTPException, e:
            logger.error('execute[%s] Mail `%s` not sent to `%s`. %s', self.ip, subject, self.mail, e)
        finally:
            server.quit()

    @property
    def _client_remote_loc(self):
        return os.path.join(self.target, cf.script)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return unicode(self.__dict__)

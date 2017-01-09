#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    同时监听多个日志文件
"""

import os
import sys
import signal
import raven
import pyinotify
from raven.transport.gevent import GeventedHTTPTransport

from log_util import FileObject


DNS_DICT = {
    "project": {
        "dns": "xx",
        "log_path": None,
    },
}


class ProcessSingleFile(pyinotify.ProcessEvent):

    def __init__(self, log, sender, tags, *args, **kwargs):
        if isinstance(log, FileObject):
            self.log = log
        else:
            self.log = FileObject(log)
        self.tags = tags
        self.sender = sender
        super(ProcessSingleFile, self).__init__(*args, **kwargs)

    def process_IN_MODIFY(self, event):
        for line in self.log.read_line():
            self.sender.captureMessage(line, tags=self.tags)


class SentryLog(object):

    def __init__(self, dns_dict, server_name, server_ip, basedir="/opt/sports"):

        if not os.path.exists(basedir):
            sys.exit()

        if not dns_dict:
            sys.exit()

        self.dns_dict = dns_dict
        self.server_name = server_name
        self.server_ip = server_ip
        self.basedir = basedir
        self.sender_dict = {}

        self.tags_dict, self.logpath_dict, self.file_dict = self.__init_info()

        self.__init_sender()
        self.wm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(self.wm)

    def __init_sender(self):

        for project, project_config in self.dns_dict.items():

            dns = project_config.get("dns")
            if dns:
                self.sender_dict[project] = raven.Client(
                    dns, transport=GeventedHTTPTransport
                )

    def __init_info(self):
        """
            根据dns配置，初始化日志文件信息
        """
        tags_dict = {}
        log_dict = {}
        file_dict = {}
        log_template = "{}/{}/logs/{}.log"

        for project, project_config in self.dns_dict.items():

            config_log_path = project_config.get("log_path")
            if not config_log_path:
                log_path = log_template.format(self.basedir, project, project)
            else:
                log_path = config_log_path

            if os.path.exists(log_path):
                tag = {
                    "name": self.server_name,
                    "ip": self.server_ip,
                    "project": project,
                    "path": log_path
                }
                # 标签
                tags_dict[project] = tag
                # 日志文件路径
                log_dict[project] = log_path
                # 日志文件
                tail_f = self.__tail_log(log_path)
                file_dict[project] = tail_f

            else:
                print "log_path: {} not find".format(log_path)

        return tags_dict, log_dict, file_dict

    def __tail_log(self, log_path):

        file = open(log_path, 'r')
        st_results = os.stat(log_path)
        st_size = st_results[6]
        file.seek(st_size)

        return FileObject(file)

    def monitor_start(self):

        for project in self.file_dict.keys():
            log_path = self.logpath_dict.get(project)
            log_file = self.file_dict.get(project)
            sender = self.sender_dict.get(project)
            tags = self.tags_dict.get(project)
            self.wm.add_watch(
                log_path, pyinotify.IN_MODIFY,
                proc_fun=ProcessSingleFile(log_file, sender, tags),
                rec=False, auto_add=False, do_glob=False,
                exclude_filter=lambda path: False)

        self.notifier.loop()

    def monitor_stop(self):
        self.notifier.stop()

    def monitor_restart(self):
        self.notifier.stop()
        self.notifier.loop()


def main():

    if len(sys.argv) == 4:
        server_name, server_ip, basedir = sys.argv[1:]
        sentry_log = SentryLog(DNS_DICT, server_name, server_ip, basedir)
    elif len(sys.argv) == 3:
        server_name, server_ip = sys.argv[1:]
        sentry_log = SentryLog(DNS_DICT, server_name, server_ip)
    else:
        print "params error"
        print "python xx.py server_name server_ip, basedir"
        sys.exit()

    sentry_log.monitor_start()

    signal.signal(signal.SIGKILL, sentry_log.monitor_stop)

if __name__ == "__main__":

    main()


import logging
import platform
import subprocess

import psutil

LOG = logging.getLogger(__name__)


def _check_platform():
    return platform.system()


class ProcessHandler(object):

    def __init__(self, proc_name):
        self.proc_name = proc_name
        if _check_platform() == 'Windows':
            self.process_name = self.process_name + '.exe'

    def _get_proc_by_name(self):
        """Get process object by a given name"""
        proc_list = [proc for proc in psutil.process_iter(
        ) if proc.name() == self.proc_name]

        if len(proc_list) == 0:
            msg = ('Unable to find process %s. Wrong process name or this\
                   process wasn\'t running' % self.proc_name)
            LOG.exception(msg)
            return None
        else:
            msg = ('List of suitable processes: %s' % proc_list)
            LOG.info(msg)
            return proc_list

    def do_method(self, method):
        """Run process's method. Check psutils docs for more detail"""
        processes = self._get_proc_by_name()

        if not processes:
            return None
        else:
            result = []
            for proc in processes:
                try:
                    result.append(getattr(proc, method))
                except Exception as e:
                    LOG.error('Process object %s doesn\'t method %s' %
                              (self.proc_name, method))
                    raise e
            return result

    def _get_executable_file(self):
        """Get executable file path, like which command in Linux"""
        exe_file = self.do_method('exe')
        LOG.info('Find executable file = %s' % exe_file)
        return exe_file


def start_application(exe_file):
    """Start application if it wasn't running"""
    try:
        subprocess.Popen(exe_file[0], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True)
        LOG.info('Start application with path = %s successfully!' % exe_file)
    except Exception as e:
        msg = ('Start application with path = %s failed!' % exe_file)
        LOG.error(msg)
        raise e

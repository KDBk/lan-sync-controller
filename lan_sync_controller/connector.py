import logging
import time

import pymysql

from lan_sync_controller.config_loader import SETTINGS

LOG = logging.getLogger(__name__)


class MySQLConnector(object):
    """Connector to MySQL.

    Will define & declare some methods for special purpose
    """

    def __init__(self):
        def _init_mysql_connection():
            try:
                LOG.info('Connecting to MySQL...')
                connection = pymysql.connect(
                    host=SETTINGS['mysql-host'],
                    port=int(SETTINGS['mysql-port']),
                    user=SETTINGS['mysql-user'],
                    password=SETTINGS['mysql-password'],
                    db=SETTINGS['mysql-db_name'],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor)
                LOG.info('Connected to MySQL!')
                return connection
            except Exception as e:
                LOG.exception('Connecting to database failed: %s', e)
                raise e

        self.connection = _init_mysql_connection()

        def __getattr__(self, key):
            return getattr(self.connection, key)

        def get_file_by_name(self, filename):
            try:
                LOG.info('Get file with name %s', filename)
                # Hardcore table name as files
                query = """select * from files 
                        where name=%s
                        """ % filename
                cursor = self.cursor()
                cursor.execute(query)
                result = self.fetchone()[0]
                LOG.info('Get file with name %s successfully!', filename)
            except Exception as e:
                LOG.exception('Fail to execute query: %s', query)
                raise e

        def insert_new_file(self, filename, filesize,
                            last_modified, version=1):
            try:
                LOG.info('Insert file with name %s', filename)
                # Hardcore table name as file_list
                query = """insert into 
                        files (name, size, last_modified, version)
                        values(%s,%s,%s,%s)
                        """ % (filename, filesize, last_modified, version)
                cursor = self.cursor()
                cursor.execute(query)
                LOG.info('Insert file with name %s successfully!', filename)
                self.commit()
            except Exception as e:
                LOG.exception('Fail to execute query: %s', query)
                raise e

        def update_file(self, filename, filesize=None, version=1):
            try:
                LOG.info('Update file with name %s', filename)
                last_modified = time.time()
                # last_modified is time in nanoseconds (Easy to compare)
                change = 'last_modified=%s' % str(last_modified)
                if filesize:
                    change += ' size=%s' % filesize
                # Hardcore table name as file_list
                query = """update files set %s 
                        where name=%s
                        """ % (change, filename)
                cursor = self.cursor()
                cursor.execute(query)
                LOG.info('Update file with name %s successfully!', filename)
                self.commit()
            except Exception as e:
                LOG.exception('Fail to execute query: %s', query)
                raise e

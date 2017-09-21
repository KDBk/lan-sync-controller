import logging

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

        def get_file_by_name(self):
            pass

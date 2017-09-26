import logging
import time

import pymysql
from keystoneauth1.identity import v3
from keystoneauth1 import session
from swiftclient.client import Connection

from lan_sync_controller.config_loader import SETTINGS

LOG = logging.getLogger(__name__)


class MySQLConnector(object):
    """Connector to MySQL.

    Will define & declare some methods for special purpose
    """

    def __init__(self):
        self.connection = self._init_mysql_connection()

    def _init_mysql_connection(self):
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

    def cleaup_database(self):
        drop_if_exist = "DROP TABLE IF EXISTS files;"
        create_new_one = """
            CREATE TABLE files (
                name VARCHAR(200) PRIMARY KEY NOT NULL,
                size INT(30),
                last_modified DOUBLE NOT NULL,
                version INT(2)
            );
        """
        try:
            cursor = self.cursor()
            LOG.info('Delete table FILES if it exists')
            cursor.execute(drop_if_exist)
            LOG.info('Recreate table FILES')
            cursor.execute(create_new_one)
        except Exception as e:
            LOG.exception('Fail to cleanup database!')
            raise e

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

    def get_files(self):
        try:
            LOG.info('Get all of files and their timlast_modifiede from server')
            # Hardcore table name as files
            query = "select name, last_modified from files"
            cursor = self.cursor()
            cursor.execute(query)
            result = self.fetchall()
        except Exception as e:
            LOG.exception('Fail to execute query: %s', query)
            raise e
        return result

    def insert_or_update(self, filename, last_modified):
        try:
            LOG.info('Create or update one row on with file name %s', filename)
            # Hardcore table name as files
            query = """
                INSERT INTO files (name, last_modified)
                VALUES ({}, {}) ON DUPLICATE KEY UPDATE last_modified = {};
            """.format(filename, last_modified, last_modified)
            cursor = self.cursor()
            cursor.execute(query)
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


class SwiftConnector(object):

    def __init__(self):
        self.connection = _init_swift_client(self)
    
    def _init_swift_client(self):
        # Keystone Authentication
        auth = v3.Password(
            auth_url=SETTINGS['swift-os_auth_url'],
            user_domain_name=SETTINGS['swift-os_user_domain_name'],
            password=SETTINGS['swift-password'],
            project_domain_name=SETTINGS['swift-os_project_domain_name'],
            project_name=SETTINGS['swift-os_project_name']
        )
        sess = session.Session(auth=auth)
        try:
            # Use version 2
            return Connection('2', session=sess)
        except Exception as e:
            LOG.exception('Connecting to Swift is failed!')
            raise e

    def upload(self, filepath):
        # Fixed container name
        LOG.info("Update file {} to Cloud server". format(filepath))
        self.connection.upload("lansync", [filepath])

    def download(self, filepath):
        # Fixed container name
        LOG.info("Download file {} from Cloud server". format(filepath))
        self.connection.upload("lansync", [filepath])

if __name__ == '__main__':
    # Recreate database to cleanup env
    mysql = MySQLConnector()
    mysql.cleaup_database()

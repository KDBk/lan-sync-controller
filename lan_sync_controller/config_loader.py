import logging
import logging.config
from six.moves import configparser

from lan_sync_controller import constants


def settings_config_loader():
    """ Load configuration from ini file"""

    parser = configparser.SafeConfigParser()
    parser.read([constants.SETTING_PATH])
    config_dict = {}

    for section in parser.sections():
        for key, value in parser.items(section, True):
            config_dict['%s-%s' % (section, key)] = value

    return config_dict


SETTINGS = settings_config_loader()


def logging_config_loader():
    logfile = SETTINGS['default-logfile']
    debug = SETTINGS['default-debug']

    logging.config.fileConfig(constants.LOGGING_PATH,
                              defaults={'logfile': logfile},
                              disable_existing_loggers=False)
    # Set root logger level depend on config.ini file
    if debug == 'True':
        root_logger = logging.root
        # Set root logger's level to DEBUG
        root_logger.setLevel(logging.DEBUG)
        # Find infoHandler and set its level to DEBUG
        for handler in root_logger.handlers:
            if handler.level == logging.INFO:
                handler.setLevel(logging.DEBUG)

# coding: utf-8
import logging
import os
import sys
import yaml


logger = logging.getLogger('concrete_datastore')


def load_datamodel(datamodel_path='current-datamodel.meta'):

    datamodel_path = os.getenv('DATAMODEL_FILE') or datamodel_path

    try:
        with open(datamodel_path, "r", encoding='utf8') as f:
            try:
                #:  Try to load datamodel with 'yaml.safe_load'.
                #:  This method loads both yaml and json files
                meta_model_definitions = yaml.safe_load(f)
            except yaml.scanner.ScannerError:
                message = (
                    f"Unable to parse datamodel file '{datamodel_path}'.\n"
                    "Please check that you specified the right filename"
                )
                logger.error(message)
                sys.exit(1)
    except IOError:
        message = (
            "You did not define a datamodel.\n"
            "You should either specify a path to a datamodel with "
            "DATAMODEL_FILE=<file_path>, or create a datamodel file "
            f"in ./datamodel named '{os.path.basename(datamodel_path)}'."
            "\nYou will find a sample file in ./datamodel"
        )
        logger.error(message)
        sys.exit(1)
    return meta_model_definitions


def get_log_path(filename):
    log_folder = os.getenv('LOG_FOLDER', os.path.join(os.getcwd(), 'log'))
    try:
        os.makedirs(log_folder)
    except FileExistsError:
        # Directory already exists
        pass
    return os.path.join(log_folder, filename)

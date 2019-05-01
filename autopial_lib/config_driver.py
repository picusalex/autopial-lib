import logging

import sys
import yaml
import os

class ConfigFile():
    def __init__(self, filename, look_in_folders=["./"], logger=None):
        self._config_loaded = False
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.load(filename, look_in_folders)

    def look_in_folder(self, ordered_folders):
        self.logger.info("Looking for '{}' config file in {}".format(self._filename, ordered_folders))
        for folder in ordered_folders:
            folder = os.path.realpath(folder)
            fullpath = os.path.join(folder, self._filename)
            if not os.path.isfile(fullpath):
                continue

            self.logger.info("Config file found: '{}'".format(fullpath))
            self._config_loaded = True
            return fullpath
        return None

    def load(self, filename, look_in_folders=["./"]):
        self._filename = filename
        configfile = self.look_in_folder(look_in_folders)
        if configfile is None:
            self.logger.error("No config file found ! Tried with:")
            for f in look_in_folders:
                self.logger.error("  {}".format(os.path.join(f, filename)))
            self._config_loaded = False
            sys.exit(1)

        self.logger.info("Loading config file: '{}'".format(configfile))
        with open(configfile, 'r') as ymlfile:
            self._cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        return True

    def get(self, *kargs, default=None):
        v = self._cfg
        for key in kargs:
            try:
                v = v[key]
            except TypeError:
                if default is None:
                    raise BaseException("Key path '{}' not found".format(":".join(kargs)))
                else:
                    return default
            except KeyError:
                if default is None:
                    raise BaseException("Key path '{}' not found".format(":".join(kargs)))
                else:
                    return default
        if isinstance(v, dict):
            if default is None:
                raise BaseException("Key path '{}' is incomplete. Please provide an additional key".format(":".join(kargs)))
            else:
                return default
        return v
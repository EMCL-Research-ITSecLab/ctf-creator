import os

from yamale.validators import DefaultValidators, Validator

class Path(Validator):
    """ Custom Path validator """
    tag = 'path'

    def _is_valid(self, value):
        return os.path.isfile(value)
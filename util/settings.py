from os import environ
from dotenv import load_dotenv

class Settings:

    def __init__(self, bool_vars: [str] = None, int_vars: [str] = None, list_vars: [str] = None):
        load_dotenv()
        self.search_prefixes = self.resolve_search_prefixes()

        self.bool_vars = bool_vars or []
        self.int_vars = int_vars or []
        self.list_vars = list_vars or []
        self.vars = {}
        pass

    @staticmethod
    def resolve_search_prefixes():

        if bool(int(environ.get('TEST_MODE', 0))):
            search_prefixes = [
                'TEST',
                'DEV'
            ]
        else:
            search_prefixes = [
                'PROD' if environ.get('RUN_MODE') == 'production' else 'DEV'
            ]
            pass

        search_prefixes.append('DEFAULT')

        return search_prefixes

    def resolve_envvar(self, key):

        for prefix in self.search_prefixes:
            k = '%s_%s' % (prefix, key)

            if k in environ:
                return environ[k]
            pass

        return None

    def __contains__(self, item):
        return self.get(item) is not None

    def __getitem__(self, key: str):
        return self.__getattr__(key)

    def __getattr__(self, item: str):
        retval = self.get(item)

        if retval is None:
            raise KeyError(item)

        return retval

    def get(self, key: str, def_val=None):

        retval = environ.get(
            key, self.vars.get(key, self.resolve_envvar(key))
        )

        if retval is not None:
            return self._cast(key, retval)

        return def_val

    def _cast(self, key: str, val: str):

        if key in self.bool_vars:
            return bool(int(val))

        if key in self.int_vars:
            return int(val)

        if key in self.list_vars:
            retval = []
            for i in val.split(','):
                retval.append(i.format_map(self))
                pass
            return retval

        return val.format_map(self)

    pass


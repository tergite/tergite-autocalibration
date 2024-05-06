import copy
from collections import abc, UserList, defaultdict
from functools import singledispatchmethod
from tergite_acl.config.settings import REDIS_CONNECTION, REDIS_PORT

def nested_dd():
    return defaultdict(nested_dd)

class AttrDict(dict):
    """A dict accessed by attribute recursivly.
       >>>d = AttrDict({'a': {'b': 1}})
       >>>d.a.b
       >>>1
       Technically speaking, it is very tricky to inherit from dict when we override __setitem__.
       But I am a bit lazy. So keep an eye out when you are using AttrDict.
    """
    
    def __getattr__(self, attr):
        #print("getattr method...")
        if attr in self.keys():
            return self.build(self[attr], attr)
        else:
            raise AttributeError(attr)
            
    def __setitem__(self, name, value):
        setattr(self, name, value)
    
    @singledispatchmethod
    def build(self, obj, attr):
        return obj
        
    @build.register(abc.Mapping)
    def _(self, obj, attr):
        cls = AttrDict
        value = cls(obj)
        dict.__setitem__(self, attr, value)
        value.__dict__['_former_instance'] = self
        value.__dict__['_key'] = attr
        return value
    
    @build.register(abc.MutableSequence)
    def _(self, obj, attr):
        cls = AttrDict
        try:
            value = [cls(item) for item in obj]
        except Exception:
            value = obj if '__dict__' in dir(obj) else UserList(obj)
        dict.__setitem__(self, attr, value)
        value.__dict__['_former_instance'] = self
        self.fresh()
        return value
    
    def __setattr__(self, attr, value):
        """Check whether attr is a descriptor in advance."""
        cls = type(self)
        if hasattr(cls, attr) and hasattr(cls.__dict__[attr], '__set__'):
            return cls.__dict__[attr].__set__(self, value)
        dict.__setitem__(self, attr, value)
        self.fresh([attr], value)
        
    def __delattr__(self, name):
        try:
            dict.__delitem__(self, name)
            self.fresh()
        except KeyError:
            raise AttributeError(name)
    
    def load(self, **kws):
        """load from file"""
        print("loading...")
        d = self.readin(**kws)
        self.update(d)
        AttrDict.set_former_instance(self)
        
    def readin(self, **kws):
        """ read in dict from file"""
        
    def _fresh(self, keys, value):
        """output into file"""
        print("freshing...")
    
    def fresh(self, keys:list, value):
        """Go to the root registry to fresh which is not 
            necessary for all cases.
        """
        try:
            keys.insert(0, self._key)
            self._former_instance.fresh(keys, value)
        except AttributeError as e:
            print(e.args)
            self._fresh(keys, value)
            
    def clear(self):
        dict.clear(self)
        self.fresh()
        
    def copy(self):
        return AttrDict(dict.copy(self))
            
    @staticmethod
    def set_former_instance(adct):
        for subadct in adct.values():
            if isinstance(subadct, abc.Mapping):
                subadct.__dict__['_former_instance'] = adct
                AttrDict.set_former_instance(subadct)
            
class SRegistry(AttrDict):
    """Simplified registry for read and write. 
    """
    def __init__(self):
        self.__dict__['cxn'] = REDIS_CONNECTION
        self.__dict__['device_dict'] = dict()
        dct = self.readin()
        super().__init__(dct)

    def fresh(self, keys, value):
        print('SRegistry starts freshing...')
        for i, key in enumerate(keys):
            if key in self.device_dict:
                keys[i] = self.device_dict[key]
        keys.append(value)
        keys = [keys[0], ":".join(keys[1:-1]), str(keys[-1])]
        self.cxn.hset(*keys)
        print('Sent to redis...')

    @staticmethod
    def _set_recr_dd(dd, key, value):
        keys_split = key.split(":")
        for key in keys_split[:-1]:
            dd = dd[key]
        try:
            dd[keys_split[-1]] = value
        except TypeError:
            dd = nested_dd()
            dd[keys_split[-1]] = value
            
    def readin(self):
        dct = nested_dd()
        for key in self.cxn.keys():
            if 'transmons' in key or 'couplers' in key:
                value_dict = self.cxn.hgetall(key)
                device = key.split(":")[-1]
                self.device_dict[device] = key
                for key, value in value_dict.items():
                    self._set_recr_dd(dct[device], key, value)
        return dct
            
    def __repr__(self):
        return f"SRegistry for redis connection binded to \n \
                 Port: {REDIS_PORT}."
        
    def copy(self):
        return SRegistry(copy.deepcopy(self))
import typing


# This is our QOI class
class QOI:

    def __init__(self,
                 name: str = None,
                 value: typing.Any = None,
                 unit: str = None):
        self.name = name
        self.value = value
        self.unit = unit  # Inspired by Tong

    def qoi_only_function(self):
        # We could do anything we want with the QOI
        pass


# This is our qoi property decorator
class qoi(property):

    def __init__(self, *args,
                 name: str = None,
                 unit: str = None,
                 value: typing.Any = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.key_name = f'_{name}'
        self.qoi_ = QOI(name=name,
                        unit=unit,
                        value=value)

    def __get__(self, *args, **kwargs):
        instance: object = args[0]
        if hasattr(instance, self.key_name):
            return instance.__getattribute__(self.key_name).value
            # We could also read from redis if we implement for sync_redis
        else:
            raise KeyError(f'QOI {self.key_name} does not exist for node {instance.__class__.__name__}')

    def __set__(self, instance, value):
        self.qoi_.value = value
        if not hasattr(instance, self.key_name):
            instance.__setattr__(self.key_name, self.qoi_)
        # We could also write to redis if we implement for sync_redis


class BaseNode:

    # Everything which is already implemented in the BaseNode

    def __init__(self):
        pass

    def get_qois(self) -> typing.Dict[str, 'QOI']:
        qoi_vars_ = list(filter(lambda key_: isinstance(self.__getattribute__(key_), QOI),
                                dir(self)))
        return {qoi_var_: self.__getattribute__(qoi_var_) for qoi_var_ in qoi_vars_}


class ExampleNode(BaseNode):
    frequency = qoi(name='frequency', unit='Hz')
    amplitude = qoi(name='amplitude', unit='m')

    # Now follows everything there is already implemented in the nodes

    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    node = ExampleNode()
    node.frequency = 3.5
    node.amplitude = 4
    print(node.frequency)
    print(node.amplitude)
    qois = node.get_qois()

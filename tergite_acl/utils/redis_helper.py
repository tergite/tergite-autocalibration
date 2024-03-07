from tergite_acl.config.settings import REDIS_CONNECTION


def fetch_redis_params(param: str, this_element: str):
    if '_' in this_element:
        name = 'couplers'
    else:
        name = 'transmons'
    redis_config = REDIS_CONNECTION.hgetall(f"{name}:{this_element}")
    return float(redis_config[param])

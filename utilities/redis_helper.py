import redis

def fetch_redis_params(param:str, this_element:str):
    redis_connection = redis.Redis(decode_responses=True)
    if '_' in this_element:
                name = 'couplers'
    else:
        name = 'transmons'
    redis_config = redis_connection.hgetall(f"{name}:{this_element}")
    return float(redis_config[param])
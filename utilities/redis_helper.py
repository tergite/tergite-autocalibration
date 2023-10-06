import redis

def fetch_redis_params(param:str, qubit:str):
    redis_connection = redis.Redis(decode_responses=True)
    redis_config = redis_connection.hgetall(f"transmons:{qubit}")
    return float(redis_config[param])
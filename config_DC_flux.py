from workers.hardware_utils import SpiDAC
import redis

redis_connection = redis.Redis(decode_responses=True)

def show_coupler_parameters(couplers):
    # couplers = [ 'q13_q14']
    couplers = [ 'q21_q22']
    for coupler in couplers: 
        print(f"Coupler parameters {coupler}:")
        redis_config = redis_connection.hgetall(f"transmons:{coupler}")
        # Print the redis config line by line
        for key, value in redis_config.items():
            print(f"{key}: {value}")

def set_coupler_current(coupler, parking_current=None):
    if parking_current is None:
        parking_current = redis_connection.hget(f'transmons:{coupler}', 'parking_current')
        if parking_current is None:
            print("Please input the parking current...")
            return
        else:
            parking_current = float(parking_current)
    else:
        #redis_connection.hset(f"transmons:{coupler}", f"{transmon_parameter}",-45e-6)
        redis_connection.hset(f"transmons:{coupler}", 'parking_current', parking_current)
    print(f"Parking current of {coupler} is ", parking_current)

def apply_coupler_current(coupler):
    DAC = SpiDAC()
    DAC.set_parking_current(coupler)

def set_dacs_zero():
    DAC = SpiDAC()
    DAC.set_dacs_zero()

# spi.set_dac_current(dac, parking_current)

# spi.set_dacs_zero()
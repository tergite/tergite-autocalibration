class Node():
    def __init__(name:str, field:str, measurement_obj, analysis_obj):
        self.name = name
        self.redis_field = field
        self.measurement = measurement_obj
        self.analysis = analysis_obj


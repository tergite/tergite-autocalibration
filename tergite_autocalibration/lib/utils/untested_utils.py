# def reset_node(self, remove_node: str, qubits: list[str]):
#     print(f"RESETING node {remove_node}")
#     transmon_configuration = toml.load(DEVICE_CONFIG)
#     quantities_of_interest = transmon_configuration["qoi"]["qubits"]
#     remove_fields = quantities_of_interest[remove_node].keys()
#     for qubit in qubits:
#         key = f"transmons:{qubit}"
#         cs_key = f"cs:{qubit}"
#         for field in remove_fields:
#             # TODO: add some checks here
#             REDIS_CONNECTION.hset(key, field, "nan")
#             structured_redis_storage(key, qubit.strip("q"), None)
#             if "motzoi" in field:
#                 REDIS_CONNECTION.hset(key, field, "0")
#                 structured_redis_storage(key, qubit.strip("q"), 0)
#         REDIS_CONNECTION.hset(cs_key, remove_node, "not_calibrated")
#
# def re_calibrate(self, node_name: str, qubits: list[str]):
#     self.reset_node(node_name, qubits)
#     print(f"RECALIBRATING node {node_name}")
#     # HACK: Importing the node_factory at runtime to avoid circular imports
#     factory = importlib.import_module(
#         "tergite_autocalibration.lib.utils.node_factory"
#     )
#     calibration_node_factory = factory.NodeFactory()
#     re_calibrating_node: BaseNode = calibration_node_factory.create_node(
#         node_name, qubits
#     )
#     is_node_calibrated = False
#     couplers = []
#     transmon_configuration = toml.load(DEVICE_CONFIG)
#     populate_node_parameters(
#         node_name,
#         is_node_calibrated,
#         transmon_configuration,
#         qubits,
#         couplers,
#         REDIS_CONNECTION,
#     )
#     data_path = create_node_data_path(re_calibrating_node)
#     re_calibrating_node.lab_instr_coordinator = self.lab_instr_coordinator
#     re_calibrating_node.calibrate(data_path)
#

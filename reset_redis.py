import redis
import toml
import argparse
from utilities import user_input
from utilities.reset_redis_node import ResetRedisNode
from nodes.node import NodeFactory

node_factory = NodeFactory()
nodes = node_factory.all_nodes()
parser = argparse.ArgumentParser()
parser.add_argument('node', choices=['all']+nodes)
args = parser.parse_args()
remove_node = args.node
reset = ResetRedisNode()
reset.reset_node(remove_node)

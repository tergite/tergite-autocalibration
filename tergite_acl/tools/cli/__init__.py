import click

from tergite_acl.utils.enums import ClusterMode


@click.group()
def cli():
    pass


@cli.group(help='Handle operations related to the cluster.')
def cluster():
    pass


@cluster.command(help='Reboot the cluster.')
def reboot():
    from qblox_instruments import Cluster
    from tergite_acl.config.settings import CLUSTER_IP

    if click.confirm('Do you really want to reboot the cluster? This operation can interrupt ongoing measurements.'):
        click.echo(f'Reboot cluster with IP:{CLUSTER_IP}')
        cluster_ = Cluster('cluster', CLUSTER_IP)
        cluster_.reboot()
    else:
        click.echo('Rebooting cluster aborted by user.')


@cli.group(help='Handle operations related to the node.')
def node():
    pass


@node.command(help='Reset all parameters in redis for the node specified.')
@click.option('-n', '--name', required=False, help='Name of the node to be reset in redis e.g resonator_spectroscopy.')
@click.option('-a', required=False, is_flag=True, help='Use -a if you want to reset all nodes.')
def reset(name, a):
    from tergite_acl.utils.reset_redis_node import ResetRedisNode

    reset_obj_ = ResetRedisNode()
    if a:
        if click.confirm('Do you really want to reset all nodes? It might take some time to recalibrate them.'):
            reset_obj_.reset_node('all')
        else:
            click.echo('Node reset aborted by user.')
    elif name is not None:
        reset_obj_.reset_node(name)
    else:
        click.echo('Please enter a node name or use the --all option to reset all nodes.')


@cli.group(help='Handle operations related to the calibration graph.')
def graph():
    pass


@graph.command(help='Plot the calibration graph to the user specified target node in topological order.')
def plot():
    from tergite_acl.lib.nodes.graph import filtered_topological_order
    from tergite_acl.utils.user_input import user_requested_calibration
    from tergite_acl.utils.visuals import draw_arrow_chart

    n_qubits = len(user_requested_calibration['all_qubits'])
    topo_order = filtered_topological_order(user_requested_calibration['target_node'])
    draw_arrow_chart(f'Qubits: {n_qubits}', topo_order)


@cli.group(help='Handle operations related to the calibration supervisor.')
def calibration():
    pass


@calibration.command(help='Start the calibration supervisor.')
@click.option('-c', '--cluster',
              required=False,
              help='Takes the cluster ip address as argument. If not set, it will try take CLUSTER_IP in the .env file.')
@click.option('-d',
              required=False,
              is_flag=True,
              help='Use -d if you want to use the dummy cluster (not implemented)')
def start(cluster_ip, is_dummy):
    from ipaddress import ip_address, IPv4Address

    from tergite_acl.config.settings import CLUSTER_IP
    from tergite_acl.scripts.calibration_supervisor import CalibrationSupervisor

    cluster_mode: 'ClusterMode' = ClusterMode.real
    parsed_cluster_ip: 'IPv4Address' = CLUSTER_IP

    # Checks whether to start the cluster in dummy mode
    # TODO: The dummy cluster is currently not implemented
    if is_dummy:
        click.echo('The option to run on a dummy cluster is currently not implemented. '
                   'Trying to start the calibration supervisor with default cluster configuration')
        cluster_mode = ClusterMode.dummy

    # Check whether the ip address of the cluster is set correctly
    if cluster_ip and not is_dummy:
        if len(cluster_ip) >= 0:
            cluster_mode = ClusterMode.real
            parsed_cluster_ip = ip_address(cluster_ip)
        else:
            click.echo('Cluster argument requires the ip address of the cluster as parameter. '
                       'Trying to start the calibration supervisor with default cluster configuration.')

    supervisor = CalibrationSupervisor(cluster_mode=cluster_mode,
                                       cluster_ip=parsed_cluster_ip)
    supervisor.calibrate_system()


@cli.command(help='Handle operations related to the well-being of the user.')
def joke():
    import asyncio
    from jokeapi import Jokes

    async def print_joke():
        j = await Jokes()  # Initialise the class
        joke_ = await j.get_joke(
            blacklist=['racist', 'religious', 'political', 'nsfw', 'sexist'])  # Retrieve a random joke
        if joke_['type'] == 'single':  # Print the joke
            print(joke_['joke'])
        else:
            print(joke_['setup'])
            print(joke_['delivery'])

    asyncio.run(print_joke())

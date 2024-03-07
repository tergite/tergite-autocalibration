import argparse


def acli_delegator():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd',
                        help='cli command to run',
                        choices=['reset_redis', 'reboot_cluster'])
    parser.add_argument('--options',
                        help='options for the cli command')
    args = parser.parse_args()
    print(args.cmd)

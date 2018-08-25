import pathlib
import subprocess
import time
import os
import sys
import argparse
import logging
import threading

from services import registry

logging.basicConfig(
    level=10, format="%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s")
log = logging.getLogger('run_resbet_service')


def main():
    parser = argparse.ArgumentParser(prog=__file__)
    parser.add_argument("--daemon-config-path",
                        help="File with daemon configuration.",
                        required=False
                        )
    args = parser.parse_args(sys.argv[1:])

    root_path = pathlib.Path(__file__).absolute().parent

    # All services modules go here
    service_modules = [
        'services.resnet_image_recognition_service'
    ]

    # Removing all previous snetd .db file
    os.system('rm *.db')

    # Call for all the services listed in service_modules
    start_all_services(root_path, service_modules, args.daemon_config_path)

    # Infinite loop to serve the services
    while True:
        try:
            time.sleep(1)
        except Exception as e:
            print(e)
            exit(0)


def start_all_services(cwd, service_modules, config_path=None):
    '''
    Loop through all service_modules and start them.
    For each one, an instance of Daemon 'snetd' is created.
    snetd will start with configs from 'snet_SERVICENAME_config.json'
    and will create a 'db_SERVICENAME.db' database file for each service.
    '''
    try:
        for i, service_module in enumerate(service_modules):
            server_name = service_module.split('.')[-1]
            print("Launching", service_module,
                  "on ports", str(registry[server_name]))

            snetd_config = None
            if config_path:
                snetd_config = pathlib.Path(
                    config_path) / ('snetd_' + server_name + '_config.json')

            processThread = threading.Thread(
                target=start_service,
                args=(cwd, service_module, snetd_config,))

            # Bind the thread with the main() to abort it when main() exits.
            processThread.daemon = True
            processThread.start()

    except Exception as e:
        print(e)
        return False

    return True


def start_service(cwd, service_module, daemon_config_file=None):
    '''
    Starts the python module of the service at the passed JSON-RPC port and
    an instance of 'snetd' for the service.
    '''
    server_name = service_module.split('.')[-1]
    jsonrpc_port = registry[server_name]['jsonrpc']
    subprocess.Popen([
        sys.executable, '-m',
        service_module,
        '--json-rpc-port',
        str(jsonrpc_port)
    ],
        cwd=str(cwd)
    )
    db_file = 'db_' + server_name + '.db'
    start_snetd(str(cwd), daemon_config_file, db_file)


def start_snetd(cwd, daemon_config_file=None, db_file=None):
    '''
    Starts the Daemon 'snetd' with:
    - Configurations from: daemon_config_file
    - Database in db_file
    '''
    cmd = ['snetd']
    if db_file is not None:
        cmd.extend(['--db-path', str(db_file)])
    if daemon_config_file is not None:
        cmd.extend(['--config', str(daemon_config_file)])
        subprocess.Popen(cmd, cwd=str(cwd))
        return True
    log.error('No Daemon config file!')
    return False


if __name__ == "__main__":
    main()
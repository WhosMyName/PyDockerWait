"""Module to check docker-composes build status and waits untill all containers are running"""

from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep
from sys import stdout as sys_stdout
import logging
from argparse import ArgumentParser, Namespace
import socket
from concurrent import futures
from datetime import datetime

LOGGER = logging.getLogger("pydockerwait")
LOG_FORMAT = "%(asctime)-15s | %(levelname)s | %(module)s%(process)d %(thread)d | %(funcName)20s() - Line %(lineno)d | %(message)s"
LOGGER.setLevel(logging.DEBUG)
STRMHDLR = logging.StreamHandler(stream=sys_stdout)
STRMHDLR.setLevel(logging.INFO)
STRMHDLR.setFormatter(logging.Formatter(LOG_FORMAT))
LOGGER.addHandler(STRMHDLR)


def __main__():
    """Mehn."""
    arg_parser: ArgumentParser = ArgumentParser(
        description="Yet another script that waits for Docker", prog="PyDockerWait"
    )
    arg_parser.add_argument(
        "-t",
        "--timeout",
        help="Timeout until PyDockerWait exits unsuccessfully",
        type=int,
        dest="timeout",
        default=120,
    )
    arg_parser.add_argument(
        "-m",
        "--host",
        "--machine",
        help="machine where the services are running on (default: localhost)",
        nargs="?",
        type=str,
        dest="host",
        default="localhost",
    )
    arg_parser.add_argument(
        "-c",
        "--container",
        help="Names of the containers to wait for",
        nargs="+",
        dest="containers",
    )
    arg_parser.add_argument(
        "-T",
        "--Threads",
        help="Amount of threads used to spawn",
        type=int,
        nargs="?",
        dest="threads",
        default=10,
    )

    args: Namespace = arg_parser.parse_args()
    executor: ThreadPoolExecutor = futures.ThreadPoolExecutor(args.threads)
    dt0: datetime = datetime.now()
    threadlist: dict = {}
    containers: list[str] = args.containers
    for container in containers:
        service_name: str = container.split(":")[0]
        service_port: int = int(container.split(":")[1])
        thread_kwargs: dict = {
            "service_name": service_name,
            "service_port": service_port,
            "service_host": args.host,
            "timeout": args.timeout,
        }
        threadlist[executor.submit(check_connection, **thread_kwargs)] = service_name
    resultlist: dict = {service.split(":")[0]: False for service in containers}
    while (datetime.now() - dt0).total_seconds() < args.timeout:
        # LOGGER.debug(f"{int((datetime.now() - dt0).total_seconds())}")
        for thread in futures.as_completed(threadlist):
            supposed_service: str = threadlist[thread]
            try:
                resultlist[supposed_service] = False
                resultlist[supposed_service] = thread.result(timeout=0.5)
            except TimeoutError:
                LOGGER.exception(f"{supposed_service} is not ready now.")
            except Exception as e:
                LOGGER.exception(f"{supposed_service} has thrown an exception:\n{e}")
        if not False in resultlist:
            break
        sleep(1)
    elapsed_time: int = int((datetime.now() - dt0).total_seconds())
    for service, state in resultlist.items():
        LOGGER.info(
            f"{service} {'was' if state else 'was not'} reachable after {elapsed_time} seconds"
        )


def check_connection(
    service_name: str, service_port: int, service_host: str, timeout: int
) -> bool:
    LOGGER.debug(
        f"Reaching {service_name} on {service_host}:{service_port} within {timeout} seconds"
    )
    conn_check: int
    for elapsed in range(0, timeout):
        try:
            sock = socket.socket()
            conn_check = sock.connect_ex((service_host, service_port))
            if conn_check == 0:
                LOGGER.info(f"{service_name} has been reached after {elapsed} seconds!")
                return True
            sleep(1)
        except Exception as e:
            LOGGER.exception(f"Exception: {e}")
        finally:
            sock.close()
    return False


if __name__ == "__main__":
    __main__()

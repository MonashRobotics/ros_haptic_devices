#!/usr/bin/env python3
# ruff: noqa: T201 S602
""" Script to make it easier to build and run a container"""
import argparse
import logging
import subprocess
import sys
from pathlib import Path

# Configuration. Change these to suit your project.
PROJECT_NAME = "ros_haptic_devices"
DOCKERFILE = "./Dockerfile"
BUILD_CONTEXT = "."


def build_image(image_name: str, dockerfile: str, build_context: str):
    """Build an image from the supplied dockerfile in the given context."""
    dockerfile_exists = Path(dockerfile).exists()
    if not dockerfile_exists:
        log.error(f"Error: {dockerfile} does not exist.")
        sys.exit()
    build_command = f"docker build {build_context} -f {dockerfile} -t {image_name}"
    log.debug(build_command)
    subprocess.run(build_command, shell=True)


def create_container(image_name: str, container_name: str):
    """
    Use 'docker run' to create a container.

    - GUI application support is enabled by setting the DISPLAY environment variable,
    and sharing the .X11-unix socket as a volume.
    - External device support is enabled by sharing /dev as a volume.
    - Full networking support is enabled by setting network mode to 'host' and
    enabling the 'privileged' flag.
    - Loading of kernel modules from inside the container is enabled by sharing
    /lib/modules as a volume.
    - Realtime scheduling support is enabled by setting ulimits
    upstream docker images.
    - The current working directory is shared as a volume inside the container.
    - The terminal is attached to the container.
    """
    run_command = f"""docker run -it \
        -e DISPLAY \
        --volume "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
        --network=host \
        --privileged \
        --volume "/dev:/dev:rw" \
        --volume "/lib/modules:/lib/modules:rw" \
        --volume "/etc/udev/rules.d:/etc/udev/rules.d:rw" \
        --volume "/run/udev:/run/udev"\
        --ulimit rtprio=99 \
        --ulimit rttime=-1 \
        --ulimit memlock=8428281856 \
        --volume "$(pwd)/geomagic/:/home/roboco/ros_ws/src/{PROJECT_NAME}" \
        --name {container_name} \
        -it {image_name} \
        bash
    """
    log.info(run_command)
    subprocess.run(run_command, shell=True)


def attach_to_container(container_name: str):
    """
    Attach the terminal to an existing container, starting it if it is currently in
    stopped state.
    """
    # Allow container to create GUI windows on the host's X server
    xhost_command = "xhost + >> /dev/null"
    log.info(xhost_command)
    subprocess.run(xhost_command, shell=True)

    if not container_is_running(container_name):
        # Start and attach to the container
        start_command = f"docker start -ia {container_name}"
        log.info(start_command)
        subprocess.run(start_command, shell=True)
    else:
        # Attach a new terminal into the running container
        program_to_run = "bash"  # you can edit this if you wish. e.g. bash -c ~/project/tmux_start.sh
        attach_command = f"docker exec -it {container_name} {program_to_run}"
        log.info(attach_command)
        subprocess.run(attach_command, shell=True)


def remove_container(container_name: str):
    """Delete the container."""
    remove_container_command = f"docker rm -f {container_name}"
    log.info(remove_container_command)
    subprocess.run(remove_container_command, shell=True)


def remove_image(image_name: str):
    """Delete the image."""
    remove_image_command = f"docker rmi -f {image_name}"
    log.info(remove_image_command)
    subprocess.run(remove_image_command, shell=True)


def command_returns_empty(command: str) -> bool:
    """Run the command and return whether or not the output was empty."""
    log.debug(command)
    output = subprocess.run(
        command, stdout=subprocess.PIPE, shell=True
    ).stdout.decode()  # run the command as if in a shell, capture stdout
    log.debug(output)
    is_empty = len(output) == 0
    return is_empty


def image_exists(image_name: str) -> bool:
    """Check if an image with the specified name has previously been built"""
    image_list_command = f"docker images -f reference={image_name} -q"
    return not command_returns_empty(image_list_command)


def container_exists(container_name: str) -> bool:
    """Check if a container with the specified name has previously been created."""
    # regex used to filter containers by exact name, rather than just substring
    container_list_command = f"docker ps -qa --no-trunc -f name=^/{container_name}$"
    return not command_returns_empty(container_list_command)


def container_is_running(container_name: str) -> bool:
    """Check if a container with the specified name is currently running."""
    # regex used to filter containers by exact name, rather than just substring
    container_list_command = f"docker ps -q --no-trunc -f name=^/{container_name}$"
    return not command_returns_empty(container_list_command)


def main(args: argparse.Namespace):
    # Set up console printing
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # Check that the project name is valid
    min_container_name_length = 2
    if len(PROJECT_NAME) < min_container_name_length:
        log.error(
            f"Error. Project name '{PROJECT_NAME}' is too short."
            "Please provide a non-empty project name of at least 2 characters."
        )
        sys.exit()

    if args.action == "run" or args.action is None:
        if not image_exists(PROJECT_NAME):
            build_image(PROJECT_NAME, DOCKERFILE, BUILD_CONTEXT)
        if not container_exists(PROJECT_NAME):
            create_container(PROJECT_NAME, PROJECT_NAME)
        else:
            attach_to_container(PROJECT_NAME)
    elif args.action == "build":
        build_image(PROJECT_NAME, DOCKERFILE, BUILD_CONTEXT)
    elif args.action == "rm":
        remove_container(PROJECT_NAME)
    elif args.action == "rmi":
        remove_image(PROJECT_NAME)


if __name__ == "__main__":
    log = logging.getLogger()
    parser = argparse.ArgumentParser(
        description="Runs docker containers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""actions:
  run (default)       run the container, building the image if necessary
  build               build the image
  rm                  remove the container
  rmi                 remove the image""",
    )

    parser.add_argument(
        "action",
        nargs="?",  # allows the parameter to be optional so we can shell by default
        help="action to perform on the container/image",
        choices=["run", "build", "rm", "rmi"],
    )
    parser.add_argument("--verbose", action="store_true", help="print debug messages")

    args = parser.parse_args()
    main(args)

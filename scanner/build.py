from subprocess import Popen, PIPE
from time import perf_counter
import datetime

DOCKER_HUB_NAMESPACE = "farcast22"


def build_and_push(image_name, dockerfile):
    # TODO add validation
    image_name = f"{DOCKER_HUB_NAMESPACE}/{image_name}"
    print(f"[{datetime.datetime.now()}] Building {image_name} from file {dockerfile}")
    build_start_time = perf_counter()
    response = Popen(f"Docker build -t {image_name} -f {dockerfile} .", stdin=PIPE, stderr=PIPE).communicate()
    dps = Popen(f"Docker ps", stdin=PIPE, stderr=PIPE, stdout=PIPE).communicate()
    r = Popen(f"Docker push {image_name}", stdin=PIPE, stderr=PIPE, stdout=PIPE).communicate()
    build_stop_time = perf_counter()
    print(f"[{datetime.datetime.now()}] Elapsed time: {build_stop_time - build_start_time} -- Completed building {image_name}")


if __name__ == '__main__':
    build_info = {"Dockerfile-nmap": "nmap", "Dockerfile-amass": "amass", "Dockerfile-discord": "amass-discord"}
    for file, image_name in build_info.items():
        build_and_push(image_name, file)

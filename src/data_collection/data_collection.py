"""키보드로 차를 조종하면서 학습용 카메라 이미지를 모으는 스크립트.

터미널에 입력된 키를 읽기 때문에 SSH 로 접속한 상태에서도 그대로 조종할 수 있다.
(sudo, keyboard 모듈, .pyc 파일이 필요 없다)

실행:  python3 data_collection.py

  w / s  : 전진 / 후진 (설정 속도로 달림, 반대 방향으로 달리던 중이면 먼저 정지)
  스페이스 : 정지 (조향은 그대로)
  q / z  : 설정 속도 올리기 / 내리기 (달리는 중이면 바로 반영)
  a / d  : 조향 왼쪽 / 오른쪽으로 한 단계
  r      : 정지하고 조향도 0 으로 초기화
  c      : 현재 카메라 화면 저장
  f      : 종료
"""
import os
import select
import signal
import sys
import termios
import time
import tty
from datetime import datetime

import cv2
import serial

#---------------Variable Setting---------------
# 아두이노 장치 이름 (ls /dev/ttyA* 명령을 터미널 창에 입력하여 확인)
SERIAL_PORT = "/dev/ttyACM0"

# 카메라 장치 번호 (ls /dev/video* 명령을 터미널 창에 입력하여 확인)
CAMERA_NUM = 0

# 저장할 이미지 크기
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480

# 최대 조향 단계 (driving.ino 의 MAX_STEERING_STEP 과 같아야 함)
MAX_STEERING = 7

# 처음 설정 속도, 최대 속도, q/z 를 한 번 누를 때 바뀌는 속도 (255 가 모터 최대)
DRIVE_SPEED = 100
MAX_SPEED = 250
SPEED_STEP = 10

# 키 입력을 반영하고 아두이노로 명령을 보내는 주기 (초)
# driving.ino 는 0.5초 동안 명령이 없으면 후륜을 멈추므로 그보다 짧아야 함
KEY_PERIOD = 0.1

# 이 시간(초) 동안 키 입력이 하나도 없으면 속도를 0 으로 만든다.
# SSH 연결이 끊겼을 때 차가 계속 달리는 것을 막기 위한 값이며, 0 이면 사용하지 않는다.
IDLE_STOP_SEC = 5.0

# 이미지를 저장할 폴더 (실행할 때마다 이 아래에 날짜-시간 폴더가 새로 생김)
DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "camera_perception_pkg", "camera_perception_pkg", "lib", "Collected_Datasets")
#----------------------------------------------


def clamp(value, low, high):
    return max(low, min(high, value))


def apply_key(key, steering, direction, drive_speed):
    """키 하나를 반영한 (조향, 진행 방향, 설정 속도) 를 돌려준다.

    진행 방향은 1(전진), 0(정지), -1(후진) 이고 실제 속도는 방향 x 설정 속도다.
    """
    if key == "w":
        # 후진 중에 누르면 바로 전진하지 않고 먼저 멈춘다 (모터·기어 보호)
        direction = 1 if direction >= 0 else 0
    elif key == "s":
        direction = -1 if direction <= 0 else 0
    elif key == " ":
        direction = 0
    elif key == "q":
        drive_speed = clamp(drive_speed + SPEED_STEP, 0, MAX_SPEED)
    elif key == "z":
        drive_speed = clamp(drive_speed - SPEED_STEP, 0, MAX_SPEED)
    elif key == "a":
        steering = clamp(steering - 1, -MAX_STEERING, MAX_STEERING)
    elif key == "d":
        steering = clamp(steering + 1, -MAX_STEERING, MAX_STEERING)
    elif key == "r":
        steering, direction = 0, 0
    return steering, direction, drive_speed


def read_keys(fd, period):
    """period 초 동안 들어온 키를 모아서 돌려준다.

    같은 키가 여러 번 들어와도 한 번으로 친다. 통신이 밀렸다가 한꺼번에 도착한
    키 때문에 속도가 갑자기 뛰는 것을 막기 위해서다.
    터미널이 닫혔으면(SSH 끊김 등) None 을 돌려준다.
    """
    keys = []
    deadline = time.monotonic() + period
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return keys
        ready, _, _ = select.select([fd], [], [], remaining)
        if not ready:
            return keys
        data = os.read(fd, 1024)
        if not data:
            return None
        for key in data.decode(errors="ignore").lower():
            if key not in keys:
                keys.append(key)


def send_command(ser, steering, speed):
    ser.write(f"s{steering}l{speed}r{speed}\n".encode())


def save_frame(cap, save_dir, frame_num, steering, speed):
    ok, frame = cap.retrieve()
    if not ok:
        print("카메라 프레임을 읽지 못해 저장하지 못했습니다.")
        return False
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"{frame_num:05d}_steer{steering}_left{speed}_right{speed}.png"
    cv2.imwrite(os.path.join(save_dir, file_name), frame)
    print(f"저장: {file_name}")
    return True


def raise_keyboard_interrupt(signum, frame):
    raise KeyboardInterrupt


def main():
    if not sys.stdin.isatty():
        sys.exit("터미널에서 직접 실행해야 키 입력을 읽을 수 있습니다.")

    cap = cv2.VideoCapture(CAMERA_NUM)
    if not cap.isOpened():
        sys.exit(f"카메라({CAMERA_NUM})를 열 수 없습니다. CAMERA_NUM 값을 확인하세요.")
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)

    ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
    time.sleep(1)  # 시리얼을 열면 아두이노가 재시작하므로 잠시 기다림

    save_dir = os.path.join(DATA_PATH, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    print(f"저장 폴더: {save_dir}")
    print("w/s 전진/후진, 스페이스 정지, q/z 설정 속도, a/d 조향, r 초기화, c 저장, f 종료")
    print(f"설정 속도: {DRIVE_SPEED}")

    # SSH 가 끊기거나(SIGHUP) 종료 신호를 받아도 아래 finally 에서 차를 멈추게 한다
    signal.signal(signal.SIGHUP, raise_keyboard_interrupt)
    signal.signal(signal.SIGTERM, raise_keyboard_interrupt)

    steering, direction, drive_speed = 0, 0, DRIVE_SPEED
    frame_num = 0
    last_key_time = time.monotonic()

    fd = sys.stdin.fileno()
    terminal_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)  # 엔터 없이 키를 바로 읽고, 누른 키를 화면에 찍지 않음
    try:
        while True:
            keys = read_keys(fd, KEY_PERIOD)
            if keys is None:
                print("터미널 연결이 끊겨 종료합니다.")
                break

            cap.grab()  # 저장할 때 오래된 화면이 나오지 않도록 계속 최신 프레임으로 갱신

            previous = (steering, direction, drive_speed)
            if keys:
                last_key_time = time.monotonic()
            for key in keys:
                steering, direction, drive_speed = apply_key(key, steering, direction, drive_speed)

            if (IDLE_STOP_SEC > 0 and direction != 0
                    and time.monotonic() - last_key_time > IDLE_STOP_SEC):
                direction = 0
                print(f"{IDLE_STOP_SEC}초 동안 키 입력이 없어 정지했습니다.")

            speed = direction * drive_speed
            send_command(ser, steering, speed)
            if (steering, direction, drive_speed) != previous:
                print(f"조향: {steering}, 속도: {speed} (설정 속도: {drive_speed})")

            if "c" in keys and save_frame(cap, save_dir, frame_num, steering, speed):
                frame_num += 1
            if "f" in keys:
                print("f 를 눌러 종료합니다.")
                break

    except KeyboardInterrupt:
        print("중단 신호를 받아 종료합니다.")
    finally:
        # 어떤 이유로 끝나든 정지 명령을 가장 먼저 보낸다
        try:
            send_command(ser, 0, 0)
            ser.flush()
            ser.close()
        except (serial.SerialException, OSError):
            pass
        cap.release()
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, terminal_settings)
            print(f"정지 명령을 보내고 종료했습니다. 저장한 이미지: {frame_num}장")
        except (termios.error, OSError):
            pass  # 터미널이 이미 닫힌 경우 (SSH 끊김)


if __name__ == "__main__":
    main()

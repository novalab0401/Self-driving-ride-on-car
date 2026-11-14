# Self-driving-ride-on-car

탑승형 전동차(ride-on car)를 ROS 2 기반 자율주행차로 만드는 프로젝트입니다.

## 구성

- `src/control/` : 아두이노 모터·조향 제어 코드
- `src/*_pkg/` : ROS 2 Humble 패키지 (카메라·라이다 인지, 판단, 시리얼 통신, 디버그, 런치)
- `src/data_collection/` : 키보드로 차를 조종하며 학습용 사진·영상을 모으는 스크립트

## 출처와 라이선스

ROS 2 패키지와 아두이노 코드는 성균관대학교 Automation Lab 의
[H-Mobility-Autonomous-Advanced-Course](https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course)
를 바탕으로 수정한 것입니다. 원본과 같은 GPL-3.0 라이선스를 따르며, 전문은 [LICENSE](LICENSE) 에 있습니다.

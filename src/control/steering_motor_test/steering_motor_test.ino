// 조향 모터 테스트: 0.3초 한쪽 → 1초 정지 → 0.3초 반대쪽 → 정지
const int STEERING_1 = 2;
const int STEERING_2 = 3;
const int SPEED = 110;      // 안 움직이면 130, 150으로 올리기
const int PULSE_MS = 300;   // 움직이는 시간

void stopMotor() {
  analogWrite(STEERING_1, 0);
  analogWrite(STEERING_2, 0);
}

void setup() {
  pinMode(STEERING_1, OUTPUT);
  pinMode(STEERING_2, OUTPUT);
  stopMotor();
  delay(2000);                       // 시작 전 2초 대기

  analogWrite(STEERING_1, SPEED);    // 첫 번째 방향
  delay(PULSE_MS);
  stopMotor();
  delay(1000);

  analogWrite(STEERING_2, SPEED);    // 반대 방향
  delay(PULSE_MS);
  stopMotor();
}

void loop() {
}
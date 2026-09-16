import random


def main():
    answer = random.randint(1, 100)
    attempts = 0

    print("1부터 100 사이의 숫자를 맞춰보세요!")

    while True:
        guess = input("숫자를 입력하세요: ")

        if not guess.isdigit():
            print("숫자만 입력해주세요.")
            continue

        guess = int(guess)
        attempts += 1

        if guess < answer:
            print("더 높은 숫자입니다.")
        elif guess > answer:
            print("더 낮은 숫자입니다.")
        else:
            print(f"정답입니다! {attempts}번 만에 맞추셨습니다. 축하합니다!")
            break


if __name__ == "__main__":
    main()

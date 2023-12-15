# Project Documentation

## Git 사용 규칙

- **Git 플로우**: release - git actions(CI/CD) - main(AWS 배포용 브랜치) - develop(개발용 브랜치) - feature branch(개인 브랜치) [[참고]](https://gmlwjd9405.github.io/2018/05/11/types-of-git-branch.html)

- 작업 시작 전 `git checkout [branch_name]`으로 본인의 branch로 이동해서 `git branch -v`로 본인의 branch로 이동되었는지 확인하고, `git merge develop`으로 branch와 develop 브랜치를 병합해서 동기화합니다. develop branch는 모든 조원의 작업들을 merge하기 때문에 계속해서 바뀌기 때문에 병합해서 동기화로 충돌을 최소화합니다. 충돌이 발생했을 때는 기본적으로 develop branch의 내용을 따르고, 본인의 branch를 develop branch에 병합을 해야한다고 생각될 경우에는 모두에게 알려주세요. 🥺

- 자신의 코드의 버전관리를 위해서 본인의 branch에 본인이 작업한 내용을 `git push origin [branch_name]`로 push합니다. 😐

- 자신의 branch에만 병합하도록 합니다. 특정 작업이 끝나면 repository에서 본인의 branch로 이동해서, pull request 버튼을 눌러서 develop branch에 병합을 요청합니다. 🙂

- `[본인의 이름].md` 파일을 만들어서 본인이 만들거나 수정한 코드에 대해서 기본적인 설명을 적어주세요. 다른 팀원들이 본인의 코드를 이해할 수 있도록 하면 좋을 것 같아요. 😊 [[참고]](https://gist.github.com/ihoneymon/652be052a0727ad59601)

- 100MB 이상의 파일은 올리면 안 됩니다. git LFS(Large File Storage)를 사용해야하는데, 굳이 쓸 필요가 없다고 생각이 되네요. 따라서 해당 파일 형식은 .gitignore에 추가해야 합니다. 🥺

- 이번 프로젝트를 통해서 모두 git 이용 방법을 확실하게 익히고 가면 좋을 거라 생각합니다. 저도 협업이 처음이라서 기본적인 규칙만 정해봤는데, 추가적인 제안 사항이 있다면 말해주세요. 😊

## 개인 branch 생성 및 사용 방법

1. 새로운 branch 생성 후 해당 브랜치로 이동

```bash
git checkout -b [branch_name]
```

2. 작업 후 모든 파일을 staging area로 이동시키기

```bash
git add .
```

3. staging area에 있는 파일들의 버전을 저장함

```
git commit -m "[commit_message]"
```

3. 처음에 자신의 branch에 push: upstream을 설정함

```bash
git push -u origin [branch_name]
```

4. 이후에 자신에 branch에 push: upstream이 설정되었으므로 -u 옵션은 불필요함

```bash
git push origin [branch_name]
```

## 가상환경 사용하기

1. 가상 환경을 생성할 경로로 이동하기

```bash
cd [path]
```

2. 가상 환경 생성

```bash
python -m venv [virtual_environment_name]
```

3. 가상 환경 활성화

```bash
[virtual_environment_path_name]\Scripts\activate
```

4. 해당 프로젝트 경로로 다시 이동하기

```bash
cd [path]
```

5. 필요한 패키지 설치하기

```bash
pip install -r requirements.txt
```

6. 가상환경 종료하기

```bash
deactivate
```

## 목소리 모델링의 기본 플로우

![Data flow](/description_images/data-flow.PNG)

## voice-changer를 docker로 설치하기

### 1. wsl 설치

- wsl 설치하기

```bash
wsl --install
```

- ubuntu 설치/재시작

```bash
wsl --install -d ubuntu
```

- wsl 설치 확인

```bash
wsl --list
```

### 2. docker desktop 설치/재시작 및 wsl와 통합하기 [[참고]](https://www.youtube.com/watch?v=POo_Cg0eFMU)

- docker desktop에서 설치하기

- 현재 사용자를 docker 그룹에 추가하기
  sudo usermod -aG docker $USER

- docker 설치 확인: docker 관련된 게 아래에 뜸

```bash
wsl --list
```

### 3. git clone

- git 모듈 다운로드: Linux git으로 clone으로 해야 띄어쓰기 이슈 예방 가능. Windows의 git pull이랑 Linux의 git pull을 했을 때, 띄어쓰기 방식이 다름.

```bash
sudo apt-get install git
```

- git clone

```bash
git clone https://github.com/w-okada/voice-changer.git
```

- git clone 한 폴더 내부로 이동하기

```bash
cd [path]
```

### 4. 프로그램 실행

- 도커를 사용해서 프로그램 실행하기: 저희 노트북에는 GPU가 없어요. 😢

```bash
USE_GPU=off bash start_docker.sh
```

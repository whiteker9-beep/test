# 아까 미리 만들어둔 "풀옵션" 이미지를 가져옴 (설치 과정 0초)
FROM asia-northeast3-docker.pkg.dev/kr-ops-vk-operations/docker-repo/kepco-crawler-base:v1

WORKDIR /app

# 소스 코드만 복사 (텍스트 파일이라 1초도 안 걸림)
COPY . .

CMD ["python", "main.py"]
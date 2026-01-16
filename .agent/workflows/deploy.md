---
description: Deploy the Spot the Difference game to jvibeschool.org/FINDSPOT
---

이 워크플로우는 프로젝트를 빌드하고 AWS 서버의 `/FINDSPOT/` 디렉토리에 배포하는 과정을 안내합니다.

// turbo-all
## 1. 프로젝트 빌드
로컬에서 최신 소스 코드를 빌드합니다.
```bash
npm run build
```

## 2. 서버 연결 설정 및 파일 전송
`dist` 폴더의 내용과 기타 정적 파일들을 서버로 전송합니다.

**서버 정보:**
- IP: `15.164.161.165`
- User: `bitnami`
- Key: `~/.ssh/jvibeschool_org.pem`
- Target Path: `/opt/bitnami/apache/htdocs/FINDSPOT/`

### 2.1 서버 디렉토리 준비
서버에 대상 디렉토리가 없다면 생성합니다.
```bash
ssh -i ~/.ssh/jvibeschool_org.pem bitnami@15.164.161.165 "sudo mkdir -p /opt/bitnami/apache/htdocs/FINDSPOT && sudo chown bitnami:bitnami /opt/bitnami/apache/htdocs/FINDSPOT"
```

### 2.2 파일 전송 (rsync)
빌드된 파일과 루트의 HTML, 설정 파일들을 전송합니다.
```bash
# dist 폴더 내용 전송
rsync -avz -e "ssh -i ~/.ssh/jvibeschool_org.pem" dist/ bitnami@15.164.161.165:/opt/bitnami/apache/htdocs/FINDSPOT/

# 루투의 개별 파일들 전송 (index.html, admin_dashboard.html, .htaccess 등)
rsync -avz -e "ssh -i ~/.ssh/jvibeschool_org.pem" index.html admin_dashboard.html game.html game_logic.js .htaccess bitnami@15.164.161.165:/opt/bitnami/apache/htdocs/FINDSPOT/

# 폴더들 전송 (public, puzzles 등)
rsync -avz -e "ssh -i ~/.ssh/jvibeschool_org.pem" public/ puzzles/ bitnami@15.164.161.165:/opt/bitnami/apache/htdocs/FINDSPOT/
```

## 3. 권한 설정
전송 후 아파치 서버가 파일을 읽을 수 있도록 권한을 재설정합니다.
```bash
ssh -i ~/.ssh/jvibeschool_org.pem bitnami@15.164.161.165 "sudo chmod -R 755 /opt/bitnami/apache/htdocs/FINDSPOT"
```

## 4. 배포 확인
브라우저에서 다음 주소로 접속하여 확인합니다:
- 메인: [https://jvibeschool.org/FINDSPOT/](https://jvibeschool.org/FINDSPOT/)
- 관리자: [https://jvibeschool.org/FINDSPOT/admin/](https://jvibeschool.org/FINDSPOT/admin/) (리다이렉트 확인)

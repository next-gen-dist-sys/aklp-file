# AKLP File Service

파일을 업로드/다운로드하고 관리하는 서비스입니다. Kubernetes 환경에서 Pod가 삭제되어도 파일이 유실되지 않도록 PostgreSQL에 파일을 저장합니다.

## 개요

| 항목           | 값                                       |
| -------------- | ---------------------------------------- |
| 포트           | `8004`                                   |
| Base URL       | `/api/v1/files`                          |
| API 문서       | [Swagger UI](http://localhost:8004/docs) |
| 데이터베이스   | `aklp_file`                              |
| 최대 파일 크기 | 10MB                                     |

## API 엔드포인트

### 1. 파일 업로드 (`POST /api/v1/files`)

**Content-Type**: `multipart/form-data`

| 필드          | 타입   | 필수 | 설명                    |
| ------------- | ------ | ---- | ----------------------- |
| `file`        | File   | O    | 업로드할 파일           |
| `description` | string | X    | 파일 설명 (최대 1000자) |
| `session_id`  | UUID   | X    | AI 세션 ID              |

```bash
curl -X POST http://localhost:8004/api/v1/files \
  -F "file=@./nginx-pod.yaml" \
  -F "description=nginx Pod 매니페스트" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440001"
```

### 2. 파일 목록 조회 (`GET /api/v1/files`)

| 파라미터     | 타입 | 설명                  |
| ------------ | ---- | --------------------- |
| `page`       | int  | 페이지 번호 (기본: 1) |
| `session_id` | UUID | 세션별 필터링         |

### 3. 파일 메타데이터 조회 (`GET /api/v1/files/{file_id}`)

파일 내용 없이 메타데이터만 조회합니다.

### 4. 파일 다운로드 (`GET /api/v1/files/{file_id}/download`)

```bash
curl -O -J http://localhost:8004/api/v1/files/{file_id}/download
```

### 5. 메타데이터 수정 (`PATCH /api/v1/files/{file_id}`)

```json
{
  "filename": "new-nginx-pod.yaml",
  "description": "수정된 설명"
}
```

### 6. 파일 교체 (`PUT /api/v1/files/{file_id}`)

기존 파일 내용을 새 파일로 완전히 교체합니다.

```bash
curl -X PUT http://localhost:8004/api/v1/files/{file_id} \
  -F "file=@./updated-nginx-pod.yaml"
```

### 7. 파일 삭제 (`DELETE /api/v1/files/{file_id}`)

---

## Agent/CLI 통합 가이드

### session_id 활용

모든 파일은 `session_id`로 AI 세션과 연결됩니다. Agent는 세션 시작 시 생성한 UUID를 모든 파일 업로드에 사용해야 합니다.

### Agent 사용 시나리오

#### 1. YAML 매니페스트 생성 및 저장

Agent가 학습용 YAML 파일을 생성하여 저장:

```bash
# 임시 파일 생성
cat > /tmp/nginx-pod.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
EOF

# 파일 업로드
curl -X POST http://localhost:8004/api/v1/files \
  -F "file=@/tmp/nginx-pod.yaml" \
  -F "description=nginx Pod 매니페스트 - 학습용" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440001"
```

#### 2. kubectl 출력 결과 저장

명령어 실행 결과를 파일로 저장:

```bash
# kubectl 출력을 파일로 저장
kubectl get pods -o yaml > /tmp/pods-status.yaml

# 업로드
curl -X POST http://localhost:8004/api/v1/files \
  -F "file=@/tmp/pods-status.yaml" \
  -F "description=현재 Pod 상태 스냅샷" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440001"
```

#### 3. 세션별 파일 목록 조회

```bash
curl "http://localhost:8004/api/v1/files?session_id=550e8400-e29b-41d4-a716-446655440001"
```

#### 4. 파일 다운로드 후 kubectl apply

```bash
# 파일 다운로드
curl -s http://localhost:8004/api/v1/files/{file_id}/download -o nginx-pod.yaml

# Kubernetes에 적용
kubectl apply -f nginx-pod.yaml
```

#### 5. 실습 과제 파일 업데이트

사용자가 수정한 파일로 교체:

```bash
curl -X PUT http://localhost:8004/api/v1/files/{file_id} \
  -F "file=@./my-nginx-pod.yaml"
```

### 권장 파일 타입

| 타입           | 확장자           | 용도                        |
| -------------- | ---------------- | --------------------------- |
| K8s 매니페스트 | `.yaml`          | Pod, Service, Deployment 등 |
| 설정 파일      | `.conf`, `.json` | ConfigMap, Secret 용 데이터 |
| 스크립트       | `.sh`            | 자동화 스크립트             |
| 로그           | `.log`, `.txt`   | kubectl logs 출력 저장      |
| 문서           | `.md`            | 학습 자료, 가이드           |

### Agent 파일 관리 패턴

```text
세션 시작
    │
    ├── Agent가 학습용 YAML 생성 → POST /files
    │
    ├── 사용자가 파일 다운로드 → GET /files/{id}/download
    │
    ├── kubectl apply 실행
    │
    ├── 실행 결과 저장 → POST /files (로그)
    │
    └── 세션 종료 시 파일 목록 정리
```

---

## 응답 형식

### 파일 메타데이터 응답

```json
{
  "id": "289b5908-19c1-483f-a020-cc3c357b37ec",
  "filename": "nginx-pod.yaml",
  "content_type": "text/yaml",
  "size": 256,
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "description": "nginx Pod 매니페스트",
  "created_at": "2025-12-06T10:00:00Z",
  "updated_at": "2025-12-06T10:00:00Z"
}
```

### 목록 응답

```json
{
  "items": [...],
  "total": 15,
  "page": 1,
  "limit": 10,
  "total_pages": 2,
  "has_next": true,
  "has_prev": false
}
```

---

## 저장 방식

현재는 PostgreSQL BYTEA를 사용하여 파일을 저장합니다.

| 특성 | 설명                                       |
| ---- | ------------------------------------------ |
| 장점 | 별도 스토리지 인프라 불필요, 트랜잭션 보장 |
| 단점 | 대용량 파일에 부적합                       |
| 제한 | 최대 10MB                                  |
| 확장 | 필요 시 Object Storage로 마이그레이션 가능 |

---

## 로컬 개발

```bash
# 의존성 설치
uv sync --all-extras

# 개발 서버 실행
uv run uvicorn app.main:app --reload --port 8004

# 마이그레이션 실행
uv run alembic upgrade head
```

## 라이선스

MIT

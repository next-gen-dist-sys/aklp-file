"""Alembic 마이그레이션 환경 설정.

이 파일은 Alembic이 데이터베이스 마이그레이션을 수행할 때 사용하는 환경을 구성합니다.
- 비동기 SQLAlchemy 엔진 사용
- 설정 파일(alembic.ini)에서 로깅 설정 로드
- app.core.config의 DATABASE_URL 사용
- 모든 모델의 메타데이터를 Base.metadata에서 수집
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings

# 모든 모델을 import하여 Base.metadata에 등록되도록 함
# 이렇게 해야 Alembic autogenerate가 모델 변경사항을 감지할 수 있음
from app.models import Base

# Alembic Config 객체 (alembic.ini 파일의 내용을 담고 있음)
config = context.config

# alembic.ini의 로깅 설정을 Python logging에 적용
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 환경 변수에서 가져온 DATABASE_URL로 alembic.ini의 sqlalchemy.url을 덮어씀
# 이를 통해 환경별(.env.compose, .env.k3s) DATABASE_URL을 사용할 수 있음
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 모델의 MetaData 객체 설정 (autogenerate 기능을 위해 필수)
# Base.metadata에는 모든 모델(Note 등)의 테이블 정보가 포함됨
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션 실행.

    오프라인 모드는 데이터베이스에 직접 연결하지 않고 SQL 스크립트를 생성합니다.
    주로 프로덕션 환경에서 DBA가 SQL을 직접 실행할 때 사용됩니다.

    사용법:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # SQL에 파라미터 값을 직접 바인딩
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """실제 마이그레이션을 실행하는 헬퍼 함수.

    Args:
        connection: 데이터베이스 연결 객체

    이 함수는 run_async_migrations에서 connection.run_sync()를 통해 호출됩니다.
    비동기 연결에서 동기 함수를 실행하기 위한 어댑터 역할을 합니다.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 방식으로 마이그레이션 실행.

    AsyncEngine을 생성하여 데이터베이스에 연결하고,
    do_run_migrations 함수를 동기 컨텍스트에서 실행합니다.

    NullPool 사용:
        마이그레이션은 일회성 작업이므로 연결 풀이 필요 없습니다.
        각 마이그레이션마다 새 연결을 생성하고 종료합니다.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 연결 풀 사용 안 함
    )

    async with connectable.connect() as connection:
        # 비동기 연결에서 동기 함수(do_run_migrations) 실행
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션 실행.

    온라인 모드는 데이터베이스에 직접 연결하여 마이그레이션을 실행합니다.
    개발 환경과 일반적인 배포 시나리오에서 사용됩니다.

    사용법:
        alembic upgrade head
        alembic downgrade -1
    """
    asyncio.run(run_async_migrations())


# 실행 모드 결정
# 일반적으로 online 모드가 사용되며, --sql 옵션 사용 시 offline 모드로 전환됩니다.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

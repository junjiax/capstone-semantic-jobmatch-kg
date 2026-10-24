"""add_vector_hnsw_index

Revision ID: d3f8abd75997
Revises: d9de3805454c
Create Date: 2026-10-23 10:48:32.962769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f8abd75997'
down_revision: Union[str, Sequence[str], None] = 'd9de3805454c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

"""
HNSW: Xây dựng đồ thị đa tầng liên kết các điểm vector lân cận.
Không cần bước huấn luyện dữ liệu ban đầu, tốc độ tìm kiếm nhanh với độ chính xác (Recall > 98%).
"""

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Tạo chỉ mục HNSW cho bảng PROFILE_SKILL
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_profile_skill_vector_hnsw
        ON "PROFILE_SKILL"
        USING hnsw ("Vector" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # Tạo chỉ mục HNSW cho bảng JD_SKILL
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_jd_skill_vector_hnsw
        ON "JD_SKILL"
        USING hnsw ("Vector" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # Tạo chỉ mục HNSW cho bảng JD
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_jd_vector_resp_hnsw
        ON "JD"
        USING hnsw ("VectorResponsibility" vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)


def downgrade() -> None:
    # Gỡ bỏ các chỉ mục khi rollback
    op.execute('DROP INDEX IF EXISTS ix_jd_vector_resp_hnsw;')
    op.execute('DROP INDEX IF EXISTS ix_jd_skill_vector_hnsw;')
    op.execute('DROP INDEX IF EXISTS ix_profile_skill_vector_hnsw;')

import logging
from app.clients.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)

CONSTRAINTS = [
    # 1. Uniqueness Constraints
    "CREATE CONSTRAINT cv_id_unique IF NOT EXISTS FOR (c:CV) REQUIRE c.cvId IS UNIQUE",
    "CREATE CONSTRAINT job_position_id_unique IF NOT EXISTS FOR (j:JobPosition) REQUIRE j.jobId IS UNIQUE",
    "CREATE CONSTRAINT jd_id_unique IF NOT EXISTS FOR (j:JD) REQUIRE j.jdId IS UNIQUE",
    "CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.skillId IS UNIQUE",
    "CREATE CONSTRAINT skill_normalized_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.normalizedName IS UNIQUE",
    "CREATE CONSTRAINT skill_req_id_unique IF NOT EXISTS FOR (sr:SkillRequirement) REQUIRE sr.requirementId IS UNIQUE",
    "CREATE CONSTRAINT domain_name_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT expertise_name_unique IF NOT EXISTS FOR (e:Expertise) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE",
    "CREATE CONSTRAINT match_result_id_unique IF NOT EXISTS FOR (m:MatchResult) REQUIRE m.matchResultId IS UNIQUE",
]

INDEXES = [
    # 2. Property Indexes
    "CREATE INDEX skill_category_idx IF NOT EXISTS FOR (s:Skill) ON (s.category)",
    "CREATE INDEX skill_name_idx IF NOT EXISTS FOR (s:Skill) ON (s.name)",
    "CREATE INDEX job_status_idx IF NOT EXISTS FOR (j:JobPosition) ON (j.status)",
    "CREATE INDEX jd_domain_idx IF NOT EXISTS FOR (j:JD) ON (j.domain)",
    "CREATE INDEX jd_expertise_idx IF NOT EXISTS FOR (j:JD) ON (j.expertise)",
    "CREATE INDEX jd_title_idx IF NOT EXISTS FOR (j:JD) ON (j.title)",
    "CREATE INDEX cv_user_id_idx IF NOT EXISTS FOR (c:CV) ON (c.userId)",
]

VECTOR_INDEXES = [
    # 3. Vector Indexes (Neo4j 5.x syntax with 384 dimensions and cosine similarity)
    """
    CREATE VECTOR INDEX cv_vector_idx IF NOT EXISTS
    FOR (c:CV) ON (c.embedding)
    OPTIONS {
      indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
      }
    }
    """,
    """
    CREATE VECTOR INDEX job_vector_idx IF NOT EXISTS
    FOR (j:JobPosition) ON (j.embedding)
    OPTIONS {
      indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
      }
    }
    """,
    """
    CREATE VECTOR INDEX jd_vector_idx IF NOT EXISTS
    FOR (j:JD) ON (j.embedding)
    OPTIONS {
      indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
      }
    }
    """
]


def init_graph_schema() -> dict:
    """
    Khởi tạo các ràng buộc duy nhất (constraints), chỉ mục tìm kiếm và vector indexes trên Neo4j.
    Hàm này có tính idempotent, có thể gọi nhiều lần an toàn mà không gây lỗi.
    """
    client = get_neo4j_client()
    created_items = {"constraints": 0, "indexes": 0, "vector_indexes": 0}

    # Execute Constraints
    for stmt in CONSTRAINTS:
        try:
            client.execute_write(stmt)
            created_items["constraints"] += 1
        except Exception as e:
            logger.warning("Constraint execution note: %s -> %s", stmt[:50], e)

    # Execute Property Indexes
    for stmt in INDEXES:
        try:
            client.execute_write(stmt)
            created_items["indexes"] += 1
        except Exception as e:
            logger.warning("Index execution note: %s -> %s", stmt[:50], e)

    # Execute Vector Indexes
    for stmt in VECTOR_INDEXES:
        try:
            client.execute_write(stmt)
            created_items["vector_indexes"] += 1
        except Exception as e:
            logger.warning("Vector index execution note: %s", e)

    logger.info("Graph schema initialized: %s", created_items)
    return created_items

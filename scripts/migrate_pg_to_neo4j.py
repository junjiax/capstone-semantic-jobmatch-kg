"""
Script ETL: Đồng bộ toàn bộ dữ liệu từ PostgreSQL sang Neo4j Knowledge Graph.
Cách chạy:
  python -m scripts.migrate_pg_to_neo4j
"""
import sys
import logging
from app.core.database import SessionLocal
from app.services.graph_service import sync_all_from_postgres, setup_knowledge_graph_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("==================================================")
    logger.info(" Bắt đầu khởi tạo & đồng bộ PostgreSQL -> Neo4j")
    logger.info("==================================================")

    # 1. Khởi tạo schema (constraints & indexes)
    logger.info("1. Thiết lập Constraints & Vector Indexes trên Neo4j...")
    schema_stats = setup_knowledge_graph_schema()
    logger.info("Kết quả schema: %s", schema_stats)

    # 2. Đồng bộ dữ liệu
    logger.info("2. Đang đọc dữ liệu từ PostgreSQL và nạp vào Neo4j...")
    db = SessionLocal()
    try:
        stats = sync_all_from_postgres(db)
        logger.info(" Đồng bộ hoàn tất thành công!")
        logger.info("Thống kê: Users=%s, Skills=%s, Jobs=%s, CVs=%s", 
                    stats.get("users"), stats.get("skills"), stats.get("jobs"), stats.get("cvs"))
    except Exception as e:
        logger.error(" Lỗi trong quá trình đồng bộ: %s", e)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

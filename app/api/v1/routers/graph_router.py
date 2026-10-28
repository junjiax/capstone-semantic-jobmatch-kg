import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_hr_or_admin
from app.api.v1.schemas.response import ResponseSchema
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.services import graph_service

logger = logging.getLogger(__name__)

router = APIRouter()


def require_cv_access(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    profile = db.query(Profile).filter(Profile.Id == cv_id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="CV không tồn tại")
    if current_user.Role != UserRole.ADMIN and profile.UserId != current_user.Id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập CV này")
    return current_user


@router.post(
    "/schema/init",
    summary="Khởi tạo Graph Schema (Constraints & Vector Indexes)",
    description="Tạo các unique constraints, property indexes và vector index 384-dim trên Neo4j. Dành cho Admin/HR.",
)
async def init_schema(
    current_user: User = Depends(require_hr_or_admin),
):
    res = graph_service.setup_knowledge_graph_schema()
    return ResponseSchema(
        success=True,
        message="Neo4j schema and indexes initialized successfully",
        data=res
    )


@router.post(
    "/sync/all",
    summary="Đồng bộ toàn bộ dữ liệu PostgreSQL sang Neo4j",
    description="Batch ETL đồng bộ Users, Skills, Jobs, CVs và các quan hệ kỹ năng sang Neo4j. Dành cho Admin/HR.",
)
async def sync_all_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    stats = graph_service.sync_all_from_postgres(db)
    return ResponseSchema(
        success=True,
        message="Full data sync to Neo4j completed",
        data=stats
    )


@router.post(
    "/sync/cv/{cv_id}",
    summary="Đồng bộ một CV sang Neo4j",
    description="Đồng bộ thông tin CV và danh sách kỹ năng của CV sang Neo4j.",
)
async def sync_single_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cv_access),
):
    success = graph_service.sync_cv_to_graph(db, cv_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể đồng bộ CV lên Graph")
    return ResponseSchema(
        success=True,
        message=f"CV {cv_id} synced to Neo4j successfully",
        data={"cvId": cv_id}
    )


@router.post(
    "/sync/job/{job_id}",
    summary="Đồng bộ một JobPosition sang Neo4j",
    description="Đồng bộ thông tin vị trí việc làm và danh sách kỹ năng yêu cầu sang Neo4j.",
)
async def sync_single_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    success = graph_service.sync_job_to_graph(db, job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể đồng bộ Job lên Graph")
    return ResponseSchema(
        success=True,
        message=f"Job {job_id} synced to Neo4j successfully",
        data={"jobId": job_id}
    )


@router.get(
    "/jobs/{job_id}/skills",
    summary="Lấy kỹ năng yêu cầu của Job từ Neo4j",
    description="Truy vấn danh sách kỹ năng yêu cầu của vị trí từ Knowledge Graph.",
)
async def get_job_skills_from_graph(
    job_id: int,
):
    from app.crud.graph.match_crud import get_job_required_skills_graph
    skills = get_job_required_skills_graph(job_id)
    return ResponseSchema(
        success=True,
        message="Job required skills retrieved from graph",
        data=skills
    )


@router.get(
    "/cvs/{cv_id}/skills",
    summary="Lấy kỹ năng của CV từ Neo4j",
    description="Truy vấn danh sách kỹ năng trích xuất của CV từ Knowledge Graph.",
)
async def get_cv_skills_from_graph(
    cv_id: int,
    current_user: User = Depends(require_cv_access),
):
    from app.crud.graph.match_crud import get_cv_skills_graph
    skills = get_cv_skills_graph(cv_id)
    return ResponseSchema(
        success=True,
        message="CV skills retrieved from graph",
        data=skills
    )


@router.get(
    "/skill-gap/{cv_id}/{job_id}",
    summary="Phân tích Skill Gap & Giải thích kết quả",
    description="Phân tích chi tiết kỹ năng đáp ứng, kỹ năng còn thiếu, kỹ năng bổ trợ, tỷ lệ bao phủ và khuyến nghị phát triển kỹ năng.",
)
async def analyze_skill_gap(
    cv_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cv_access),
):
    analysis = graph_service.get_skill_gap_analysis_service(db, cv_id, job_id)
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    return ResponseSchema(
        success=True,
        message="Skill gap analysis completed successfully",
        data=analysis
    )


@router.get(
    "/jobs/{job_id}/candidates",
    summary="Tìm ứng viên phù hợp bằng Hybrid Search (Vector + Graph)",
    description="Tìm kiếm và xếp hạng ứng viên tiềm năng kết hợp Vector Index và Graph Skill Coverage.",
)
async def find_candidates_for_job(
    job_id: int,
    top_k: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin),
):
    candidates = graph_service.hybrid_search_candidates_service(db, job_id, top_k)
    return ResponseSchema(
        success=True,
        message=f"Top {len(candidates)} candidates retrieved for job {job_id}",
        data=candidates
    )


@router.post(
    "/match/{cv_id}/{jd_id}",
    summary="BÀI TOÁN 1: So khớp 1 CV vs 1 JD -> Điểm số thực [0, 1]",
    description="Trả lời câu hỏi: CV của tôi có phù hợp để apply vào job này không? Tính toán độ tương hợp đa chiều [0, 1] và lưu quan hệ MATCHES_JD lên Knowledge Graph.",
)
async def match_cv_jd(
    cv_id: int,
    jd_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cv_access),
):
    result = graph_service.calculate_cv_jd_matching_service(db, cv_id, jd_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return ResponseSchema(
        success=True,
        message=f"CV {cv_id} matching with JD {jd_id} completed",
        data=result
    )


@router.get(
    "/matrix/domain-gap/{cv_id}",
    summary="BÀI TOÁN 2: Ma trận tương quan Domain & Skill Gap (1 CV vs Many Domains)",
    description="Trả lời câu hỏi: CV của tôi có thể apply vào những domain nào trong CNTT? Trả về ma trận N * K với các giá trị trong [0, 1], xếp hạng Domain và gợi ý bù đắp khoảng cách kỹ năng.",
)
async def get_domain_matrix_gap(
    cv_id: int,
    target_domains: Optional[List[str]] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cv_access),
):
    matrix_res = graph_service.calculate_domain_skill_gap_matrix_service(db, cv_id, target_domains)
    if "error" in matrix_res:
        raise HTTPException(status_code=404, detail=matrix_res["error"])
    return ResponseSchema(
        success=True,
        message=f"Domain correlation matrix generated for CV {cv_id}",
        data=matrix_res
    )


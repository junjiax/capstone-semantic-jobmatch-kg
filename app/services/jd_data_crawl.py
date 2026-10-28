from PLAYWRIGHT import sync_playwright


LINKEDIN_URL = "https://www.linkedin.com.vn"
CAREERVIET_URL = "https://www.careerviet.vn"

# ---------------------------------
# --------- CRAWL JD DATA---------
# ---------------------------------
def crawl_jd_data(db: Session, jd_data: Dict[str, Any]) -> JD:
    """Thu thập danh sách JD mới."""
    jd = job_crud.create_jd(db, **jd_data)
    return jd

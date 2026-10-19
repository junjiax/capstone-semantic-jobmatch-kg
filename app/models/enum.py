import enum

class CVFileType(enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class ProfileFileType(str, enum.Enum):
    PDF = "pdf"
    OTHER = "other"

class JobStatus(enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    DELETED = "deleted"

class EducationLevel(enum.Enum):
    HIGH_SCHOOL = "high_school"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"

class BatchStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UserRole(str , enum.Enum):
    CANDIDATE = "candidate"
    ADMIN = "admin"
    APPLICANT = "candidate"
    HR = "admin"

class UserStatus(str, enum.Enum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    BANNED   = "banned"
    PENDING  = "pending"
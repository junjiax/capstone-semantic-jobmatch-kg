import enum

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class CVFileType(enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

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
    HR = "hr"
    APPLICANT = "applicant"
    ADMIN     = "admin"

class UserStatus(str, enum.Enum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    BANNED   = "banned"
    PENDING  = "pending"
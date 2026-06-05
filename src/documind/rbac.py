from enum import Enum
from documind.database import get_connection

class AccessLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SALARY_TIER = "salary_tier"
    HIRING_MANAGER = "hiring_manager"
    C_SUITE = "c_suite"


class UserRole(str, Enum):
    PUBLIC_USER = "public_user"
    CANDIDATE = "candidate"
    JUNIOR_EMPLOYEE = "junior_employee"
    HIRING_MANAGER = "hiring_manager"
    HR = "hr"
    ADMIN = "admin"
    C_SUITE = "c_suite"

ACCESS_MATRIX: dict[UserRole, set[AccessLevel]] = {
    UserRole.PUBLIC_USER: {AccessLevel.PUBLIC},
    UserRole.CANDIDATE: {AccessLevel.PUBLIC},
    UserRole.JUNIOR_EMPLOYEE: {AccessLevel.PUBLIC, AccessLevel.INTERNAL},
    UserRole.HIRING_MANAGER: {AccessLevel.PUBLIC, AccessLevel.INTERNAL, AccessLevel.SALARY_TIER, AccessLevel.HIRING_MANAGER},
    UserRole.HR: {AccessLevel.PUBLIC, AccessLevel.INTERNAL, AccessLevel.SALARY_TIER},
    UserRole.ADMIN: set(AccessLevel),  
    UserRole.C_SUITE: set(AccessLevel),  
}

class AccessController():
    def get_user_role(self, user_id: str, tenant_id: str)->UserRole:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role FROM user_roles WHERE user_id = %s AND tenant_id = %s", (user_id, tenant_id))
                row = cur.fetchone()
        if row is None: 
            return UserRole.PUBLIC_USER
        return UserRole(row[0])
    
    def get_accessible_levels(self, role: UserRole)->set[AccessLevel]:
        return ACCESS_MATRIX[role]
    
    def get_accessible_document_ids(self, user_id: str, tenant_id: str)->list[str]:
        user_role = self.get_user_role(user_id, tenant_id)
        levels = [lvl.value for lvl in self.get_accessible_levels(user_role)]

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT document_id FROM documents WHERE tenant_id = %s AND access_level = ANY(%s)", (tenant_id, levels),)
                rows = cur.fetchall()
        return [r[0] for r in rows]


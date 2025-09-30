"""
身分驗證相關依賴（向後相容）
"""
# 為了向後相容，從新的中介軟體模組匯入
from app.middleware.auth import (
    get_current_user_id,
    get_current_user,
    get_current_user_optional,
    require_roles,
    require_permission,
    RoleChecker,
    PermissionChecker,
    AdminOnly,
    VictimOnly,
    OfficialOrgOnly,
    SupplyManagerOnly,
    VolunteerAndAbove,
    CanCreateTask,
    CanClaimTask,
    CanManageSupplies,
    CanCreateNeed
)
"""Insert initial data

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert user roles
    op.execute("""
        INSERT INTO user_roles (role, display_name, permissions) VALUES
        ('admin', '系統管理員', '{"all": true}'),
        ('victim', '受災戶', '{"create_need": true, "view_shelters": true}'),
        ('official_org', '正式志工組織', '{"create_task": true, "claim_task": true, "manage_supplies": true}'),
        ('unofficial_org', '非正式志工組織', '{"create_task": false, "claim_task": true}'),
        ('supply_manager', '物資站點管理者', '{"manage_supplies": true, "create_task": true}'),
        ('volunteer', '一般志工', '{"claim_task": true}')
    """)

    # Insert task types
    op.execute("""
        INSERT INTO task_types (type, display_name, description) VALUES
        ('cleanup', '清理工作', '災後清理、垃圾清運等工作'),
        ('rescue', '救援任務', '人員搜救、緊急救援'),
        ('supply_delivery', '物資配送', '物資運送、分發工作'),
        ('medical_aid', '醫療協助', '醫療救護、健康檢查'),
        ('shelter_support', '避難所支援', '避難所管理、服務工作')
    """)

    # Insert task statuses
    op.execute("""
        INSERT INTO task_statuses (status, display_name, description) VALUES
        ('pending', '待審核', '等待管理員審核'),
        ('available', '可認領', '可供志工認領的任務'),
        ('claimed', '已認領', '已被志工認領'),
        ('in_progress', '執行中', '正在執行的任務'),
        ('completed', '已完成', '已完成的任務'),
        ('cancelled', '已取消', '已取消的任務')
    """)

    # Insert need types
    op.execute("""
        INSERT INTO need_types (type, display_name, description) VALUES
        ('food', '食物需求', '食品、飲水等基本需求'),
        ('medical', '醫療需求', '醫療用品、藥品需求'),
        ('shelter', '住宿需求', '臨時住所、避難需求'),
        ('clothing', '衣物需求', '衣服、棉被等保暖用品'),
        ('rescue', '救援需求', '人員搜救、緊急救援'),
        ('cleanup', '清理需求', '環境清理、修繕協助')
    """)

    # Insert need statuses
    op.execute("""
        INSERT INTO need_statuses (status, display_name, description) VALUES
        ('open', '待處理', '新發布的需求'),
        ('assigned', '已分配', '已分配給志工處理'),
        ('in_progress', '處理中', '正在處理的需求'),
        ('resolved', '已解決', '已解決的需求'),
        ('closed', '已關閉', '已關閉的需求')
    """)

    # Insert supply types
    op.execute("""
        INSERT INTO supply_types (type, display_name, category, unit) VALUES
        ('water', '飲用水', 'food', 'bottle'),
        ('rice', '白米', 'food', 'kg'),
        ('instant_noodles', '泡麵', 'food', 'pack'),
        ('blanket', '毛毯', 'clothing', 'piece'),
        ('first_aid_kit', '急救包', 'medical', 'kit'),
        ('flashlight', '手電筒', 'tools', 'piece'),
        ('battery', '電池', 'tools', 'pack'),
        ('candle', '蠟燭', 'tools', 'piece'),
        ('medicine', '常用藥品', 'medical', 'box'),
        ('clothing', '衣物', 'clothing', 'piece')
    """)

    # Insert reservation statuses
    op.execute("""
        INSERT INTO reservation_statuses (status, display_name, description) VALUES
        ('pending', '待確認', '等待物資站點確認'),
        ('confirmed', '已確認', '物資站點已確認'),
        ('ready', '待領取', '物資已準備好可領取'),
        ('picked_up', '已領取', '物資已被領取'),
        ('delivered', '已配送', '物資已配送完成'),
        ('cancelled', '已取消', '預訂已取消')
    """)


def downgrade() -> None:
    # Delete initial data in reverse order
    op.execute("DELETE FROM reservation_statuses")
    op.execute("DELETE FROM supply_types")
    op.execute("DELETE FROM need_statuses")
    op.execute("DELETE FROM need_types")
    op.execute("DELETE FROM task_statuses")
    op.execute("DELETE FROM task_types")
    op.execute("DELETE FROM user_roles")
import { UserRole, TaskStatus, NeedStatus, TaskType, NeedType } from '@/types';

// 用戶角色顯示名稱
export const USER_ROLE_LABELS = {
  [UserRole.ADMIN]: '系統管理員',
  [UserRole.VICTIM]: '受災戶',
  [UserRole.VOLUNTEER]: '一般志工',
  [UserRole.OFFICIAL_ORG]: '正式志工組織',
  [UserRole.UNOFFICIAL_ORG]: '非正式志工組織',
  [UserRole.SUPPLY_MANAGER]: '物資站點管理者',
};

// 任務狀態顯示名稱
export const TASK_STATUS_LABELS = {
  [TaskStatus.PENDING]: '待審核',
  [TaskStatus.AVAILABLE]: '可認領',
  [TaskStatus.CLAIMED]: '已認領',
  [TaskStatus.IN_PROGRESS]: '執行中',
  [TaskStatus.COMPLETED]: '已完成',
  [TaskStatus.CANCELLED]: '已取消',
};

// 任務狀態顏色
export const TASK_STATUS_COLORS = {
  [TaskStatus.PENDING]: 'orange',
  [TaskStatus.AVAILABLE]: 'blue',
  [TaskStatus.CLAIMED]: 'cyan',
  [TaskStatus.IN_PROGRESS]: 'purple',
  [TaskStatus.COMPLETED]: 'green',
  [TaskStatus.CANCELLED]: 'red',
};

// 需求狀態顯示名稱
export const NEED_STATUS_LABELS = {
  [NeedStatus.OPEN]: '待處理',
  [NeedStatus.ASSIGNED]: '已分配',
  [NeedStatus.IN_PROGRESS]: '處理中',
  [NeedStatus.RESOLVED]: '已解決',
  [NeedStatus.CLOSED]: '已關閉',
};

// 需求狀態顏色
export const NEED_STATUS_COLORS = {
  [NeedStatus.OPEN]: 'red',
  [NeedStatus.ASSIGNED]: 'orange',
  [NeedStatus.IN_PROGRESS]: 'blue',
  [NeedStatus.RESOLVED]: 'green',
  [NeedStatus.CLOSED]: 'default',
};

// 任務類型顯示名稱
export const TASK_TYPE_LABELS = {
  [TaskType.CLEANUP]: '清理工作',
  [TaskType.RESCUE]: '救援任務',
  [TaskType.SUPPLY_DELIVERY]: '物資配送',
  [TaskType.MEDICAL_AID]: '醫療協助',
  [TaskType.SHELTER_SUPPORT]: '避難所支援',
};

// 需求類型顯示名稱
export const NEED_TYPE_LABELS = {
  [NeedType.FOOD]: '食物需求',
  [NeedType.MEDICAL]: '醫療需求',
  [NeedType.SHELTER]: '住宿需求',
  [NeedType.CLOTHING]: '衣物需求',
  [NeedType.RESCUE]: '救援需求',
  [NeedType.CLEANUP]: '清理需求',
};

// 緊急程度
export const URGENCY_LEVELS = {
  1: { label: '低', color: 'green' },
  2: { label: '中低', color: 'lime' },
  3: { label: '中', color: 'orange' },
  4: { label: '高', color: 'red' },
  5: { label: '緊急', color: 'magenta' },
};

// 優先級
export const PRIORITY_LEVELS = {
  1: { label: '低', color: 'default' },
  2: { label: '中低', color: 'blue' },
  3: { label: '中', color: 'orange' },
  4: { label: '高', color: 'red' },
  5: { label: '最高', color: 'magenta' },
};

// API 端點
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
    LOGOUT: '/auth/logout',
  },
  TASKS: {
    LIST: '/tasks',
    CREATE: '/tasks',
    DETAIL: (id: string) => `/tasks/${id}`,
    CLAIM: (id: string) => `/tasks/${id}/claim`,
    UPDATE_STATUS: (id: string) => `/tasks/${id}/status`,
  },
  NEEDS: {
    LIST: '/needs',
    CREATE: '/needs',
    DETAIL: (id: string) => `/needs/${id}`,
    ASSIGN: (id: string) => `/needs/${id}/assign`,
    UPDATE_STATUS: (id: string) => `/needs/${id}/status`,
  },
  SUPPLIES: {
    STATIONS: '/supplies/stations',
    INVENTORY: (stationId: string) => `/supplies/stations/${stationId}/inventory`,
    RESERVATIONS: '/supplies/reservations',
  },
  NOTIFICATIONS: {
    LIST: '/notifications',
    MARK_READ: (id: string) => `/notifications/${id}/read`,
    UNREAD_COUNT: '/notifications/unread-count',
  },
};

// 分頁設定
export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: ['10', '20', '50', '100'],
  SHOW_SIZE_CHANGER: true,
  SHOW_QUICK_JUMPER: true,
};

// 地圖設定
export const MAP_CONFIG = {
  DEFAULT_CENTER: [23.9739, 121.6015], // 花蓮光復鄉座標
  DEFAULT_ZOOM: 13,
  TILE_LAYER_URL: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  ATTRIBUTION: '© OpenStreetMap contributors',
};
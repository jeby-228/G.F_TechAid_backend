// 用戶相關類型
export enum UserRole {
  ADMIN = 'admin',
  VICTIM = 'victim',
  OFFICIAL_ORG = 'official_org',
  UNOFFICIAL_ORG = 'unofficial_org',
  SUPPLY_MANAGER = 'supply_manager',
  VOLUNTEER = 'volunteer'
}

export interface User {
  id: string;
  email: string;
  phone?: string;
  name: string;
  role: UserRole;
  isApproved: boolean;
  profileData?: any;
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  phone?: string;
  role: UserRole;
}

// 任務相關類型
export enum TaskStatus {
  PENDING = 'pending',
  AVAILABLE = 'available',
  CLAIMED = 'claimed',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export enum TaskType {
  CLEANUP = 'cleanup',
  RESCUE = 'rescue',
  SUPPLY_DELIVERY = 'supply_delivery',
  MEDICAL_AID = 'medical_aid',
  SHELTER_SUPPORT = 'shelter_support'
}

export interface Task {
  id: string;
  creatorId: string;
  title: string;
  description: string;
  taskType: TaskType;
  status: TaskStatus;
  locationData: LocationData;
  requiredVolunteers: number;
  requiredSkills?: string[];
  deadline?: string;
  priorityLevel: number;
  createdAt: string;
  updatedAt: string;
}

// 需求相關類型
export enum NeedStatus {
  OPEN = 'open',
  ASSIGNED = 'assigned',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
  CLOSED = 'closed'
}

export enum NeedType {
  FOOD = 'food',
  MEDICAL = 'medical',
  SHELTER = 'shelter',
  CLOTHING = 'clothing',
  RESCUE = 'rescue',
  CLEANUP = 'cleanup'
}

export interface Need {
  id: string;
  reporterId: string;
  title: string;
  description: string;
  needType: NeedType;
  status: NeedStatus;
  locationData: LocationData;
  requirements: any;
  urgencyLevel: number;
  contactInfo?: any;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
}

// 物資相關類型
export interface SupplyStation {
  id: string;
  managerId: string;
  name: string;
  address: string;
  locationData: LocationData;
  contactInfo: any;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface InventoryItem {
  id: string;
  stationId: string;
  supplyType: string;
  description: string;
  isAvailable: boolean;
  notes?: string;
  updatedAt: string;
}

export interface SupplyReservation {
  id: string;
  userId: string;
  stationId: string;
  taskId?: string;
  needId?: string;
  status: string;
  reservedAt: string;
  confirmedAt?: string;
  pickedUpAt?: string;
  deliveredAt?: string;
  notes?: string;
}

// 地理位置相關類型
export interface Coordinates {
  lat: number;
  lng: number;
}

export interface LocationData {
  address: string;
  coordinates: Coordinates;
  details?: string;
}

// 通知相關類型
export interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  notificationType: string;
  relatedId?: string;
  isRead: boolean;
  sentAt: string;
  readAt?: string;
}

// API 回應類型
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 錯誤類型
export interface ApiError {
  errorCode: string;
  message: string;
  details?: any;
  timestamp: string;
  requestId: string;
}
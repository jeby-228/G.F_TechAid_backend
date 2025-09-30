import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Button,
  Typography,
  Input,
  Space,
  Tag,
  Row,
  Col,
  Avatar,
  Divider,
  message,
  Empty,
  Spin,
  Modal,
  Form,
  InputNumber,
  Select,
  Tabs
} from 'antd';
import {
  ShopOutlined,
  EnvironmentOutlined,
  PhoneOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  SearchOutlined,
  ShoppingCartOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { SupplyStation, InventoryItem, SupplyReservation, UserRole } from '@/types';
import { apiClient } from '@/services/api';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

const SuppliesPage: React.FC = () => {
  const [stations, setStations] = useState<SupplyStation[]>([]);
  const [reservations, setReservations] = useState<SupplyReservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [selectedStation, setSelectedStation] = useState<SupplyStation | null>(null);
  const [stationInventory, setStationInventory] = useState<InventoryItem[]>([]);
  const [reservationModalVisible, setReservationModalVisible] = useState(false);
  const [reservationForm] = Form.useForm();
  const { user } = useSelector((state: RootState) => state.auth);

  const supplyTypes = [
    { value: 'water', label: '飲用水', icon: '💧' },
    { value: 'rice', label: '白米', icon: '🍚' },
    { value: 'instant_noodles', label: '泡麵', icon: '🍜' },
    { value: 'blanket', label: '毛毯', icon: '🛏️' },
    { value: 'first_aid_kit', label: '急救包', icon: '🏥' },
    { value: 'flashlight', label: '手電筒', icon: '🔦' },
    { value: 'clothing', label: '衣物', icon: '👕' },
    { value: 'medicine', label: '藥品', icon: '💊' }
  ];

  useEffect(() => {
    fetchStations();
    if (canViewReservations()) {
      fetchReservations();
    }
  }, []);

  const fetchStations = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get<SupplyStation[]>('/supply-stations');
      setStations(response.data);
    } catch (error) {
      message.error('載入物資站點失敗');
    } finally {
      setLoading(false);
    }
  };

  const fetchReservations = async () => {
    try {
      const response = await apiClient.get<SupplyReservation[]>('/supply-reservations/my');
      setReservations(response.data);
    } catch (error) {
      message.error('載入預訂記錄失敗');
    }
  };

  const fetchStationInventory = async (stationId: string) => {
    try {
      const response = await apiClient.get<InventoryItem[]>(`/supply-stations/${stationId}/inventory`);
      setStationInventory(response.data);
    } catch (error) {
      message.error('載入庫存資訊失敗');
    }
  };

  const handleStationClick = async (station: SupplyStation) => {
    setSelectedStation(station);
    await fetchStationInventory(station.id);
  };

  const handleReservation = async (values: any) => {
    try {
      await apiClient.post('/supply-reservations', {
        stationId: selectedStation?.id,
        items: values.items,
        notes: values.notes
      });
      message.success('物資預訂成功，請等待站點確認');
      setReservationModalVisible(false);
      reservationForm.resetFields();
      fetchReservations();
    } catch (error) {
      message.error('預訂失敗，請重試');
    }
  };

  const canViewReservations = () => {
    return user && [UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG].includes(user.role);
  };

  const canMakeReservation = () => {
    return user && [UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG].includes(user.role);
  };

  const getSupplyTypeLabel = (type: string) => {
    const supplyType = supplyTypes.find(s => s.value === type);
    return supplyType ? `${supplyType.icon} ${supplyType.label}` : type;
  };

  const getReservationStatusColor = (status: string) => {
    const statusMap: { [key: string]: string } = {
      'pending': 'orange',
      'confirmed': 'blue',
      'ready': 'green',
      'completed': 'default',
      'cancelled': 'red'
    };
    return statusMap[status] || 'default';
  };

  const getReservationStatusText = (status: string) => {
    const statusMap: { [key: string]: string } = {
      'pending': '待確認',
      'confirmed': '已確認',
      'ready': '可領取',
      'completed': '已完成',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  };

  const filteredStations = stations.filter(station =>
    station.name.toLowerCase().includes(searchText.toLowerCase()) ||
    station.address.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>物資站點</Title>
        <Text type="secondary">查看物資站點位置和庫存資訊</Text>
      </div>

      <Tabs defaultActiveKey="list">
        <TabPane tab="站點列表" key="list">
          <Card style={{ marginBottom: 24 }}>
            <Search
              placeholder="搜尋站點名稱或地址"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }}
            />
          </Card>

          <Row gutter={16}>
            <Col xs={24} lg={selectedStation ? 12 : 24}>
              <Spin spinning={loading}>
                {filteredStations.length === 0 ? (
                  <Empty description="暫無物資站點" />
                ) : (
                  <List
                    grid={{ gutter: 16, column: selectedStation ? 1 : 2 }}
                    dataSource={filteredStations}
                    renderItem={(station) => (
                      <List.Item>
                        <Card
                          hoverable
                          onClick={() => handleStationClick(station)}
                          style={{
                            border: selectedStation?.id === station.id ? '2px solid #1890ff' : undefined
                          }}
                        >
                          <Card.Meta
                            avatar={
                              <Avatar
                                style={{ backgroundColor: '#52c41a' }}
                                icon={<ShopOutlined />}
                              />
                            }
                            title={station.name}
                            description={
                              <Space direction="vertical" size={4}>
                                <Space size={4}>
                                  <EnvironmentOutlined style={{ color: '#666' }} />
                                  <Text type="secondary">{station.address}</Text>
                                </Space>
                                <Space size={4}>
                                  <PhoneOutlined style={{ color: '#666' }} />
                                  <Text type="secondary">
                                    {station.contactInfo?.phone || '聯絡資訊待更新'}
                                  </Text>
                                </Space>
                                <Tag color={station.isActive ? 'green' : 'red'}>
                                  {station.isActive ? '營運中' : '暫停服務'}
                                </Tag>
                              </Space>
                            }
                          />
                        </Card>
                      </List.Item>
                    )}
                  />
                )}
              </Spin>
            </Col>

            {selectedStation && (
              <Col xs={24} lg={12}>
                <Card
                  title={`${selectedStation.name} - 庫存資訊`}
                  extra={
                    canMakeReservation() && (
                      <Button
                        type="primary"
                        icon={<ShoppingCartOutlined />}
                        onClick={() => setReservationModalVisible(true)}
                      >
                        預訂物資
                      </Button>
                    )
                  }
                >
                  {stationInventory.length === 0 ? (
                    <Empty description="暫無庫存資訊" />
                  ) : (
                    <List
                      dataSource={stationInventory}
                      renderItem={(item) => (
                        <List.Item>
                          <List.Item.Meta
                            title={getSupplyTypeLabel(item.supplyType)}
                            description={
                              <Space direction="vertical" size={4}>
                                {item.description && <Text>{item.description}</Text>}
                                {item.notes && <Text type="secondary">{item.notes}</Text>}
                                <Tag color={item.isAvailable ? 'green' : 'red'}>
                                  {item.isAvailable ? '有庫存' : '缺貨'}
                                </Tag>
                              </Space>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  )}
                </Card>
              </Col>
            )}
          </Row>
        </TabPane>

        <TabPane tab="地圖檢視" key="map">
          <Card>
            <div style={{ height: 500 }}>
              <MapContainer
                center={[23.9739, 121.6015]}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {filteredStations.map((station) => (
                  <Marker
                    key={station.id}
                    position={[station.locationData.coordinates.lat, station.locationData.coordinates.lng]}
                  >
                    <Popup>
                      <div>
                        <strong>{station.name}</strong>
                        <br />
                        {station.address}
                        <br />
                        <Tag color={station.isActive ? 'green' : 'red'}>
                          {station.isActive ? '營運中' : '暫停服務'}
                        </Tag>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </Card>
        </TabPane>

        {canViewReservations() && (
          <TabPane tab="我的預訂" key="reservations">
            <List
              dataSource={reservations}
              renderItem={(reservation) => (
                <List.Item>
                  <Card style={{ width: '100%' }}>
                    <Row justify="space-between" align="middle">
                      <Col>
                        <Space direction="vertical" size={4}>
                          <Text strong>預訂編號: {reservation.id.slice(0, 8)}</Text>
                          <Text>站點: {stations.find(s => s.id === reservation.stationId)?.name}</Text>
                          <Text type="secondary">
                            預訂時間: {new Date(reservation.reservedAt).toLocaleString('zh-TW')}
                          </Text>
                          {reservation.notes && <Text type="secondary">備註: {reservation.notes}</Text>}
                        </Space>
                      </Col>
                      <Col>
                        <Tag color={getReservationStatusColor(reservation.status)}>
                          {getReservationStatusText(reservation.status)}
                        </Tag>
                      </Col>
                    </Row>
                  </Card>
                </List.Item>
              )}
            />
          </TabPane>
        )}
      </Tabs>

      <Modal
        title="預訂物資"
        open={reservationModalVisible}
        onCancel={() => setReservationModalVisible(false)}
        footer={null}
      >
        <Form
          form={reservationForm}
          onFinish={handleReservation}
          layout="vertical"
        >
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Row key={key} gutter={16} align="middle">
                    <Col span={10}>
                      <Form.Item
                        {...restField}
                        name={[name, 'supplyType']}
                        rules={[{ required: true, message: '請選擇物資類型' }]}
                      >
                        <Select placeholder="選擇物資">
                          {stationInventory
                            .filter(item => item.isAvailable)
                            .map(item => (
                              <Option key={item.supplyType} value={item.supplyType}>
                                {getSupplyTypeLabel(item.supplyType)}
                              </Option>
                            ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        {...restField}
                        name={[name, 'quantity']}
                        rules={[{ required: true, message: '請輸入數量' }]}
                      >
                        <InputNumber
                          min={1}
                          placeholder="數量"
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Button onClick={() => remove(name)} danger>
                        移除
                      </Button>
                    </Col>
                  </Row>
                ))}
                <Form.Item>
                  <Button
                    type="dashed"
                    onClick={() => add()}
                    block
                    icon={<PlusOutlined />}
                  >
                    新增物資項目
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Form.Item name="notes" label="備註">
            <Input.TextArea placeholder="特殊需求或備註" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                提交預訂
              </Button>
              <Button onClick={() => setReservationModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SuppliesPage;
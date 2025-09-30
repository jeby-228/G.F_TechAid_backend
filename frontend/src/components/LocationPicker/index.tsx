import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import { LatLng } from 'leaflet';
import { Input, Space, Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { LocationData, Coordinates } from '@/types';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.divIcon({
  html: `<div style="background-color: #1890ff; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface LocationPickerProps {
  onLocationSelect: (location: LocationData) => void;
  initialLocation?: LocationData | null;
  height?: number;
}

interface MapClickHandlerProps {
  onLocationSelect: (location: LocationData) => void;
}

const MapClickHandler: React.FC<MapClickHandlerProps> = ({ onLocationSelect }) => {
  useMapEvents({
    click: async (e) => {
      const { lat, lng } = e.latlng;
      
      // In a real implementation, you would use a geocoding service here
      // For now, we'll create a simple location object
      const locationData: LocationData = {
        address: `緯度: ${lat.toFixed(6)}, 經度: ${lng.toFixed(6)}`,
        coordinates: { lat, lng },
        details: '地圖選點'
      };
      
      onLocationSelect(locationData);
    },
  });
  
  return null;
};

const LocationPicker: React.FC<LocationPickerProps> = ({
  onLocationSelect,
  initialLocation,
  height = 300
}) => {
  const [searchAddress, setSearchAddress] = useState('');
  const [mapCenter, setMapCenter] = useState<Coordinates>({ lat: 23.9739, lng: 121.6015 }); // 花蓮光復鄉
  const [selectedPosition, setSelectedPosition] = useState<Coordinates | null>(
    initialLocation?.coordinates || null
  );

  useEffect(() => {
    if (initialLocation?.coordinates) {
      setMapCenter(initialLocation.coordinates);
      setSelectedPosition(initialLocation.coordinates);
    }
  }, [initialLocation]);

  const handleSearch = async () => {
    if (!searchAddress.trim()) return;
    
    // In a real implementation, you would use a geocoding service
    // For demo purposes, we'll just show a message
    console.log('搜尋地址:', searchAddress);
    // This would typically call a geocoding API and update the map center
  };

  const handleLocationSelect = (location: LocationData) => {
    setSelectedPosition(location.coordinates);
    onLocationSelect(location);
  };

  return (
    <div style={{ width: '100%' }}>
      <Space.Compact style={{ width: '100%', marginBottom: 12 }}>
        <Input
          placeholder="輸入地址搜尋"
          value={searchAddress}
          onChange={(e) => setSearchAddress(e.target.value)}
          onPressEnter={handleSearch}
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={handleSearch}
        >
          搜尋
        </Button>
      </Space.Compact>
      
      <div style={{ height, border: '1px solid #d9d9d9', borderRadius: 6 }}>
        <MapContainer
          center={[mapCenter.lat, mapCenter.lng]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <MapClickHandler onLocationSelect={handleLocationSelect} />
          
          {selectedPosition && (
            <Marker position={[selectedPosition.lat, selectedPosition.lng]} />
          )}
        </MapContainer>
      </div>
      
      <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
        點擊地圖選擇位置，或使用上方搜尋功能
      </div>
    </div>
  );
};

export default LocationPicker;
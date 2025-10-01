import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import LocationPicker from '../index';
import { LocationData } from '@/types';

// Mock react-leaflet components
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ position }: any) => (
    <div data-testid="marker" data-position={`${position[0]},${position[1]}`} />
  ),
  useMapEvents: ({ click }: any) => {
    // Simulate map click for testing
    React.useEffect(() => {
      const handleClick = () => {
        click({
          latlng: { lat: 23.9739, lng: 121.6015 }
        });
      };
      
      // Add click listener to map container
      const mapContainer = document.querySelector('[data-testid="map-container"]');
      if (mapContainer) {
        mapContainer.addEventListener('click', handleClick);
        return () => mapContainer.removeEventListener('click', handleClick);
      }
    }, []);
    
    return null;
  }
}));

// Mock leaflet CSS import
jest.mock('leaflet/dist/leaflet.css', () => ({}));

// Mock leaflet
jest.mock('leaflet', () => ({
  divIcon: jest.fn(() => ({})),
  Marker: {
    prototype: {
      options: {}
    }
  }
}));

describe('LocationPicker', () => {
  const mockOnLocationSelect = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders location picker with map', () => {
    render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    expect(screen.getByPlaceholderText('輸入地址搜尋')).toBeInTheDocument();
    expect(screen.getByText('搜尋')).toBeInTheDocument();
    expect(screen.getByTestId('map-container')).toBeInTheDocument();
    expect(screen.getByText('點擊地圖選擇位置，或使用上方搜尋功能')).toBeInTheDocument();
  });

  test('handles search input', () => {
    render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    const searchInput = screen.getByPlaceholderText('輸入地址搜尋');
    fireEvent.change(searchInput, { target: { value: '花蓮縣光復鄉' } });
    
    expect(searchInput).toHaveValue('花蓮縣光復鄉');
  });

  test('handles search button click', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    const searchInput = screen.getByPlaceholderText('輸入地址搜尋');
    fireEvent.change(searchInput, { target: { value: '花蓮縣光復鄉' } });
    
    const searchButton = screen.getByText('搜尋');
    fireEvent.click(searchButton);
    
    expect(consoleSpy).toHaveBeenCalledWith('搜尋地址:', '花蓮縣光復鄉');
    
    consoleSpy.mockRestore();
  });

  test('handles search on enter key', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    const searchInput = screen.getByPlaceholderText('輸入地址搜尋');
    fireEvent.change(searchInput, { target: { value: '花蓮縣光復鄉' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });
    
    expect(consoleSpy).toHaveBeenCalledWith('搜尋地址:', '花蓮縣光復鄉');
    
    consoleSpy.mockRestore();
  });

  test('does not search with empty input', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    
    render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    const searchButton = screen.getByText('搜尋');
    fireEvent.click(searchButton);
    
    expect(consoleSpy).not.toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });

  test('shows initial location when provided', () => {
    const initialLocation: LocationData = {
      address: '花蓮縣光復鄉',
      coordinates: { lat: 23.9739, lng: 121.6015 },
      details: '測試位置'
    };
    
    render(
      <LocationPicker 
        onLocationSelect={mockOnLocationSelect} 
        initialLocation={initialLocation}
      />
    );
    
    expect(screen.getByTestId('marker')).toHaveAttribute(
      'data-position', 
      '23.9739,121.6015'
    );
  });

  test('handles map click and calls onLocationSelect', () => {
    render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    const mapContainer = screen.getByTestId('map-container');
    fireEvent.click(mapContainer);
    
    expect(mockOnLocationSelect).toHaveBeenCalledWith({
      address: '緯度: 23.973900, 經度: 121.601500',
      coordinates: { lat: 23.9739, lng: 121.6015 },
      details: '地圖選點'
    });
  });

  test('renders with custom height', () => {
    const { container } = render(
      <LocationPicker 
        onLocationSelect={mockOnLocationSelect} 
        height={400}
      />
    );
    
    const mapWrapper = container.querySelector('[style*="height: 400px"]');
    expect(mapWrapper).toBeInTheDocument();
  });

  test('uses default height when not specified', () => {
    const { container } = render(
      <LocationPicker onLocationSelect={mockOnLocationSelect} />
    );
    
    const mapWrapper = container.querySelector('[style*="height: 300px"]');
    expect(mapWrapper).toBeInTheDocument();
  });
});
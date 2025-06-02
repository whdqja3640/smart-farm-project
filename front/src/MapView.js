import React, { useEffect, useRef, useState } from 'react';

const MapView = () => {
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const mapInstance = useRef(null);

  // 지도 초기화
  useEffect(() => {
    const initMap = () => {
      const container = mapRef.current;
      const options = {
        center: new window.kakao.maps.LatLng(37.5665, 126.9780),
        level: 3,
      };
      const map = new window.kakao.maps.Map(container, options);
      mapInstance.current = map;

      const marker = new window.kakao.maps.Marker({
        position: options.center,
        map: map,
      });
      markerRef.current = marker;
    };

    if (window.kakao && window.kakao.maps) {
      window.kakao.maps.load(initMap);
    }
  }, []);

  // 실시간 위치 fetch 및 마커 갱신
  useEffect(() => {
    const fetchPosition = async () => {
      try {
        const res = await fetch('https://mature-grub-climbing.ngrok-free.app/get-path');
        const data = await res.json();

        if (data.length > 0) {
          const latest = data[data.length - 1];
          const newPos = new window.kakao.maps.LatLng(latest.lat, latest.lon);

          if (markerRef.current) {
            markerRef.current.setPosition(newPos);
          }

          if (mapInstance.current) {
            mapInstance.current.setCenter(newPos);
          }
        }
      } catch (error) {
        console.error('GPS 수신 실패:', error);
      }
    };

    const interval = setInterval(fetchPosition, 5001);
    return () => clearInterval(interval);
  }, []);

  return <div ref={mapRef} style={{ width: '100%', height: '800px' }} />;
};

export default MapView;

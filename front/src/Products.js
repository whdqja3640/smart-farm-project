import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Products.css';
import API_BASE_URL from './config';

function Products() {
  const [devices, setDevices] = useState([]);
  const navigate = useNavigate();

  const loadDevices = () => {
    fetch(`${API_BASE_URL}/product/my_devices`, {
      credentials: "include"
    })
      .then(res => res.json())
      .then(data => {
        if (data.devices) {
          setDevices(data.devices);
        }
      })
      .catch(err => console.error("구독 목록 불러오기 실패:", err));
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const handleSubscribe = () => {
    navigate('/iot-setting');
  };

  const handleUnsubscribe = async (id) => {
    const confirmed = window.confirm("정말 구독을 취소하시겠습니까?");
    if (!confirmed) return;

    try {
      const res = await fetch(`${API_BASE_URL}/product/unsubscribe/${id}`, {
        method: "DELETE",
        credentials: "include"
      });
      const data = await res.json();
      alert(data.message);
      loadDevices();
    } catch (err) {
      alert("❌ 구독 취소 실패");
      console.error(err);
    }
  };

  return (
    <div className="products-container">
      <table className="products-table">
        <tbody>
          <tr>
            <td valign="top" width="300">
              <h3 className="products-title">내 IOT 구독</h3>
              {devices.length === 0 ? (
                <p>아직 구독한 기기가 없습니다.</p>
              ) : (
                <ul className="products-list">
                  {devices.map((device) => (
                    <li key={device.id} style={{ marginBottom: '10px' }}>
                      <strong>📷 {device.iot_name}</strong>
                      <div style={{ marginTop: '5px' }}>
                        <button
                          style={{ marginRight: '8px', padding: '4px 8px' }}
                          onClick={() => navigate(`/iot-setting/${device.id}`)}
                        >
                          수정
                        </button>
                        <button
                          style={{
                            padding: '4px 8px',
                            backgroundColor: '#ff5c5c',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px'
                          }}
                          onClick={() => handleUnsubscribe(device.id)}
                        >
                          구독 취소
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </td>
            <td valign="top" className="products-subscribe-section">
              <h2 className="products-subscribe-title">IOT 구독</h2>
              <button className="products-subscribe-btn" onClick={handleSubscribe}>구독하기</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default Products;
// 카카오맵 WebView 컴포넌트 - 앱에서 카카오맵 표시

import React from "react";
import { StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";

interface MarkerInfo {
  lat: number;
  lng: number;
  type: string;
  name: string;
  markerId: string;
  kakaoPlaceId?: string;
  aptSeq?: string;
}

interface PolygonInfo {
  code: string;
  grade: number;
  name: string;
  value: number;
}

interface KakaoMapProps {
  lat: number;
  lng: number;
  level?: number;
  markers?: MarkerInfo[];
  onMarkerClick?: (marker: MarkerInfo) => void;
  polygons?: PolygonInfo[];
  geoJson?: any;
  highlightOnly?: boolean;
}

const KAKAO_APP_KEY = "644f705c07c7107a5ab76925f451797a";

const KakaoMap: React.FC<KakaoMapProps> = ({
  lat,
  lng,
  level = 3,
  markers = [],
  onMarkerClick,
  polygons = [],
  geoJson,
  highlightOnly = false,
}) => {
  const markerColors: Record<string, string> = {
    subway: "#3CB44B",
    mart: "#E67E22",
    department: "#9B59B6",
    hospital: "#E74C3C",
    school: "#3498DB",
    apartment: "#E74C3C",
  };

  const gradeColors: Record<number, string> = {
    1: "#93C6E7",
    2: "#4A90D9",
    3: "#5BAD6F",
    4: "#E8A838",
    5: "#D9534F",
  };

  // React 레벨에서 미리 해당 동 좌표만 추출
  const dongCoordsArr = (() => {
    if (!geoJson || !highlightOnly || polygons.length === 0) return [];
    const targetName = polygons[0]?.name || '';
    const fullAddress = polygons[0]?.code || '';
    const guMatch = fullAddress.match(/([가-힣]+구)/);
    const targetGu = guMatch ? guMatch[1] : null;
    console.log('targetGu:', targetGu, '/ fullAddress:', fullAddress);
    // 1순위: 구 정보 있으면 구까지 매칭
    if (targetGu) {
      const guExact = geoJson.features.filter((f: any) =>
        f.properties.name === targetName && f.properties.adm_nm?.includes(targetGu)
      );
      if (guExact.length > 0) return guExact.map((f: any) => f.geometry.coordinates[0]);
      // 구 정보 있는데 정확매칭 실패 시 바로 퍼지로 (다른 구 삼성동에 걸리는 것 방지)
      const cleaned2 = targetName.replace(/동([0-9가])/g, '$1').replace(/동$/, '');
      if (cleaned2.length >= 2) {
        const guFuzzy = geoJson.features.filter((f: any) => {
          if (!f.properties.adm_nm?.includes(targetGu)) return false;
          const fname = f.properties.name.replace(/동$/, '');
          return fname.includes(cleaned2) || cleaned2.includes(fname);
        });
        if (guFuzzy.length > 0) return guFuzzy.map((f: any) => f.geometry.coordinates[0]);
      }
    }
    // 2순위: 정확 매칭 (구 정보 없을 때만)
    if (!targetGu) {
      const exact = geoJson.features.filter((f: any) => f.properties.name === targetName);
      if (exact.length > 0) return exact.map((f: any) => f.geometry.coordinates[0]);
    }
    const cleaned = targetName.replace(/동([0-9가])/g, '$1').replace(/동$/, '');
    if (cleaned.length < 2) return [];
    const fuzzy = geoJson.features.filter((f: any) => {
      if (targetGu && f.properties.adm_nm && !f.properties.adm_nm.includes(targetGu)) return false;
      const fname = f.properties.name.replace(/동$/, '');
      return fname.includes(cleaned) || cleaned.includes(fname);
    });
    return fuzzy.map((f: any) => f.geometry.coordinates[0]);
  })();
  const dongCoords = dongCoordsArr.length > 0 ? dongCoordsArr[0] : null;

  const pipScript = dongCoordsArr.length > 0 ? `
    function pointInPolygon(lat, lng, polygonCoords) {
      var inside = false;
      for (var i = 0, j = polygonCoords.length - 1; i < polygonCoords.length; j = i++) {
        var xi = polygonCoords[i][1], yi = polygonCoords[i][0];
        var xj = polygonCoords[j][1], yj = polygonCoords[j][0];
        var intersect = ((yi > lng) != (yj > lng)) && (lat < (xj - xi) * (lng - yi) / (yj - yi) + xi);
        if (intersect) inside = !inside;
      }
      return inside;
    }
    window._dongPolygonCoords = ${JSON.stringify(dongCoords)};
    // highlightOnly 동 경계 직접 그리기
    (function() {
      var allCoords = ${JSON.stringify(dongCoordsArr)};
      allCoords.forEach(function(coords) {
        var path = coords.map(function(c) { return new kakao.maps.LatLng(c[1], c[0]); });
        new kakao.maps.Polygon({
          path: path,
          strokeWeight: 2,
          strokeColor: "#2563EB",
          strokeOpacity: 0.9,
          fillColor: "#2563EB",
          fillOpacity: 0.15,
        }).setMap(map);
      });
    })();
  ` : "";

  const polygonScript = geoJson && polygons.length > 0 ? `
    (function() {
      var gradeColors = {1: "#93C6E7", 2: "#4A90D9", 3: "#5BAD6F", 4: "#E8A838", 5: "#D9534F"};
      var polygonData = ${JSON.stringify(polygons)};
      var gradeMap = {};
      var nameMap = {};
      var valueMap = {};
      polygonData.forEach(function(p) { 
        gradeMap[p.code] = p.grade;
        nameMap[p.code] = p.name;
        valueMap[p.code] = p.value;
      });
      var features = ${JSON.stringify(geoJson.features)};
      if (${JSON.stringify(highlightOnly)}) {
        features = features.filter(function(f) { return gradeMap[f.properties.name] !== undefined; });
      }
      features.forEach(function(feature) {
        var code = feature.properties.name;
        var grade = gradeMap[code] || 3;
        var color = gradeColors[grade] || "#5BAD6F";
        var coords = feature.geometry.coordinates[0];
        var path = coords.map(function(c) { return new kakao.maps.LatLng(c[1], c[0]); });
        var isHighlight = ${JSON.stringify(highlightOnly)};
        var polygon = new kakao.maps.Polygon({
          path: path,
          strokeWeight: isHighlight ? 2 : 1,
          strokeColor: isHighlight ? "#2563EB" : "#FFFFFF",
          strokeOpacity: 0.9,
          fillColor: isHighlight ? "#2563EB" : color,
          fillOpacity: isHighlight ? 0.15 : 0.6,
        });
        polygon.setMap(map);
        kakao.maps.event.addListener(polygon, 'mouseover', function() {
          polygon.setOptions({ fillOpacity: 0.85 });
        });
        kakao.maps.event.addListener(polygon, 'mouseout', function() {
          polygon.setOptions({ fillOpacity: 0.6 });
        });
      });
    })();
  ` : "";

  const markerScript = markers
    .filter((m) => !m.markerId.endsWith("_none") && m.lat && m.lng)
    .filter((m) => {
      // highlightOnly 모드에서 infra 마커는 동 경계 안에 있는지 나중에 JS에서 필터링
      return true;
    })
    .map((m) => {
      const color = markerColors[m.type] || "#888";
      const isApartment = m.type === "apartment";
      return `
        (function() {
          var el = document.createElement('div');
          el.style.cssText = 'width:${isApartment ? "14px" : "12px"};height:${isApartment ? "14px" : "12px"};background:${color};border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4);cursor:pointer;position:relative;';
          var pos = new kakao.maps.LatLng(${m.lat}, ${m.lng});
          var overlay = new kakao.maps.CustomOverlay({ position: pos, content: el, yAnchor: 1 });
          overlay.setMap(map);

          ${!isApartment && !highlightOnly ? `
          new kakao.maps.Polyline({
            path: [new kakao.maps.LatLng(${lat}, ${lng}), pos],
            strokeWeight: 2.5,
            strokeColor: '${color}',
            strokeOpacity: 0.7,
            strokeStyle: 'shortdot',
          }).setMap(map);
          ` : ""}

          // highlightOnly 모드에서 동 경계 밖 인프라 마커 숨김
          if (${JSON.stringify(highlightOnly)} && !${JSON.stringify(m.type === 'apartment')}) {
            if (window._dongPolygonCoords) {
              var _inside = false;
              var _lat = ${m.lat}, _lng = ${m.lng};
              var _coords = window._dongPolygonCoords;
              for (var _i = 0, _j = _coords.length - 1; _i < _coords.length; _j = _i++) {
                var _xi = _coords[_i][1], _yi = _coords[_i][0];
                var _xj = _coords[_j][1], _yj = _coords[_j][0];
                var _int = ((_yi > _lng) != (_yj > _lng)) && (_lat < (_xj - _xi) * (_lng - _yi) / (_yj - _yi) + _xi);
                if (_int) _inside = !_inside;
              }
              if (!_inside) { return; }
            }
          }
          el.addEventListener('click', function() {
            ${isApartment ? `
            // 아파트 마커 클릭 시 이름 표시 후 React Native로 이벤트 전달
            var existing = document.getElementById('label-${m.markerId}');
            if (existing) {
              existing.remove();
              return;
            }
            var label = document.createElement('div');
            label.id = 'label-${m.markerId}';
            label.style.cssText = 'position:absolute;background:white;border:1px solid #ddd;border-radius:6px;padding:4px 8px;font-size:11px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.2);transform:translate(-50%,-150%);cursor:pointer;z-index:100;';
            label.innerText = '${m.name.replace(/'/g, "\\'")} >';
            label.addEventListener('click', function(e) {
              e.stopPropagation();
              window.ReactNativeWebView.postMessage(JSON.stringify({
                type: 'markerClick',
                markerId: '${m.markerId}',
                name: '${m.name.replace(/'/g, "\\'")}',
                lat: ${m.lat},
                lng: ${m.lng},
                kakaoPlaceId: '${m.kakaoPlaceId || ""}',
                aptSeq: '${m.aptSeq || ""}',
              }));
            });
            el.appendChild(label);
            ` : `
            var existing = document.getElementById('label-${m.markerId}');
            if (existing) { existing.remove(); return; }
            var label = document.createElement('div');
            label.id = 'label-${m.markerId}';
            label.style.cssText = 'position:absolute;background:white;border:1px solid #ddd;border-radius:6px;padding:3px 7px;font-size:11px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.2);transform:translate(-50%,-130%);pointer-events:none;';
            label.innerText = '${m.name.replace(/'/g, "\\'")}';
            el.appendChild(label);
            `}
          });
        })();
      `;
    })
    .join("\n");

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
      <style>
        * { margin: 0; padding: 0; }
        html, body { width: 100%; height: 100%; }
        #map { width: 100%; height: 100%; }
        #zoom-controls {
          position: absolute;
          right: 10px;
          bottom: 30px;
          z-index: 10;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .zoom-btn {
          width: 32px;
          height: 32px;
          background: white;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 18px;
          font-weight: 300;
          color: #333;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 1px 3px rgba(0,0,0,0.2);
          line-height: 1;
        }
      </style>
      <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_APP_KEY}&autoload=false"></script>
    </head>
    <body>
      <div id="map"></div>
      <div id="zoom-controls">
        <button class="zoom-btn" onclick="zoomIn()">+</button>
        <button class="zoom-btn" onclick="zoomOut()">−</button>
      </div>
      ${polygons.length > 0 && !highlightOnly ? `<div id="legend" style="position:absolute;left:10px;bottom:30px;z-index:10;background:white;border:1px solid #ddd;border-radius:8px;padding:8px 10px;font-size:11px;box-shadow:0 1px 3px rgba(0,0,0,0.2);">
        <div style="margin-bottom:3px;font-weight:600;color:#333;font-size:11px;">평균가</div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#D9534F;"></div><span style="color:#555;">높음</span></div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#E8A838;"></div><span style="color:#555;"></span></div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#5BAD6F;"></div><span style="color:#555;">중간</span></div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#4A90D9;"></div><span style="color:#555;"></span></div>
        <div style="display:flex;align-items:center;gap:5px;"><div style="width:12px;height:12px;border-radius:2px;background:#93C6E7;"></div><span style="color:#555;">낮음</span></div>
      </div>` : ''}
      <script>
        var map;
        kakao.maps.load(function() {
          var options = {
            center: new kakao.maps.LatLng(${lat}, ${lng}),
            level: ${level}
          };
          map = new kakao.maps.Map(document.getElementById('map'), options);
          new kakao.maps.Marker({
            position: new kakao.maps.LatLng(${lat}, ${lng}),
            map: map
          });
          ${pipScript}
          ${polygonScript}
          ${markerScript}
        });

        function zoomIn() {
          if (map) map.setLevel(map.getLevel() - 1);
        }
        function zoomOut() {
          if (map) map.setLevel(map.getLevel() + 1);
        }
      </script>
    </body>
    </html>
  `;

  return (
    <View style={styles.container}>
      <WebView
        source={{ html }}
        style={styles.map}
        scrollEnabled={false}
        javaScriptEnabled={true}
        originWhitelist={["*"]}
        onMessage={(event) => {
          if (onMarkerClick) {
            try {
              const data = JSON.parse(event.nativeEvent.data);
              if (data.type === "markerClick") {
                onMarkerClick(data);
              }
            } catch (e) {}
          }
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 10,
    height: 340,
    borderRadius: 14,
    overflow: "hidden",
    borderWidth: 0.5,
    borderColor: "#E5E5E5",
  },
  map: { flex: 1 },
});

export default React.memo<KakaoMapProps>(KakaoMap);
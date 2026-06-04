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
        var polygon = new kakao.maps.Polygon({
          path: path,
          strokeWeight: 1,
          strokeColor: "#FFFFFF",
          strokeOpacity: 0.8,
          fillColor: color,
          fillOpacity: 0.6,
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

          ${!isApartment ? `
          new kakao.maps.Polyline({
            path: [new kakao.maps.LatLng(${lat}, ${lng}), pos],
            strokeWeight: 2.5,
            strokeColor: '${color}',
            strokeOpacity: 0.7,
            strokeStyle: 'shortdot',
          }).setMap(map);
          ` : ""}

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
      <div id="legend" style="position:absolute;left:10px;bottom:30px;z-index:10;background:white;border:1px solid #ddd;border-radius:8px;padding:8px 10px;font-size:11px;box-shadow:0 1px 3px rgba(0,0,0,0.2);">
        <div style="margin-bottom:3px;font-weight:600;color:#333;font-size:11px;">평균가</div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#D9534F;"></div><span style="color:#555;">높음</span></div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#E8A838;"></div><span style="color:#555;"></span></div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#5BAD6F;"></div><span style="color:#555;">중간</span></div>
        <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:12px;height:12px;border-radius:2px;background:#4A90D9;"></div><span style="color:#555;"></span></div>
        <div style="display:flex;align-items:center;gap:5px;"><div style="width:12px;height:12px;border-radius:2px;background:#93C6E7;"></div><span style="color:#555;">낮음</span></div>
      </div>
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
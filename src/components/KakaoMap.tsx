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
}

interface KakaoMapProps {
  lat: number;
  lng: number;
  level?: number;
  markers?: MarkerInfo[];
}

const KAKAO_APP_KEY = "644f705c07c7107a5ab76925f451797a";

const KakaoMap: React.FC<KakaoMapProps> = ({
  lat,
  lng,
  level = 3,
  markers = [],
}) => {
  const markerColors: Record<string, string> = {
    subway: "#3CB44B",
    mart: "#E67E22",
    department: "#9B59B6",
    hospital: "#E74C3C",
    school: "#3498DB",
  };

  // 인프라 마커 JS 코드 생성
  const markerScript = markers
    .filter((m) => !m.markerId.endsWith("_none") && m.lat && m.lng)
    .map((m) => {
      const color = markerColors[m.type] || "#888";
      return `
        (function() {
          var el = document.createElement('div');
          el.style.cssText = 'width:12px;height:12px;background:${color};border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4);cursor:pointer;position:relative;';
          var pos = new kakao.maps.LatLng(${m.lat}, ${m.lng});
          var overlay = new kakao.maps.CustomOverlay({ position: pos, content: el, yAnchor: 1 });
          overlay.setMap(map);
          el.addEventListener('click', function() {
            var existing = document.getElementById('label-${m.markerId}');
            if (existing) { existing.remove(); return; }
            var label = document.createElement('div');
            label.id = 'label-${m.markerId}';
            label.style.cssText = 'position:absolute;background:white;border:1px solid #ddd;border-radius:6px;padding:3px 7px;font-size:11px;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.2);transform:translate(-50%,-130%);pointer-events:none;';
            label.innerText = '${m.name.replace(/'/g, "\\'")}';
            el.appendChild(label);
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
    borderColor: "#E8E5DA",
  },
  map: { flex: 1 },
});

export default KakaoMap;

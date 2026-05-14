const fs = require("fs");
const path = require("path");

const indexPath = path.join(__dirname, "dist", "index.html");
let html = fs.readFileSync(indexPath, "utf-8");

const kakaoScript = `<script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=644f705c07c7107a5ab76925f451797a&autoload=false"></script>`;

if (!html.includes("dapi.kakao.com")) {
  html = html.replace("</head>", `${kakaoScript}</head>`);
  fs.writeFileSync(indexPath, html);
  console.log("카카오맵 SDK 주입 완료");
} else {
  console.log("이미 주입됨");
}

// 캐시 비활성화 설정
const serveConfig = {
  headers: [
    {
      source: "**",
      headers: [
        {
          key: "Cache-Control",
          value: "no-cache, no-store, must-revalidate",
        },
      ],
    },
  ],
};

fs.writeFileSync(
  path.join(__dirname, "dist", "serve.json"),
  JSON.stringify(serveConfig, null, 2),
);
console.log("캐시 설정 완료");

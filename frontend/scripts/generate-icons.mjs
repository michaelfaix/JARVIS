import sharp from "sharp";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "..", "public");

async function generateIcon(size) {
  const fontSize = Math.round(size * 0.52);
  const yOffset = Math.round(size * 0.05);
  const cornerRadius = Math.round(size * 0.18);

  const svg = `
  <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#2563eb"/>
        <stop offset="100%" stop-color="#1d4ed8"/>
      </linearGradient>
    </defs>
    <rect width="${size}" height="${size}" rx="${cornerRadius}" fill="url(#bg)"/>
    <text
      x="50%" y="${50 + yOffset}%"
      text-anchor="middle"
      dominant-baseline="central"
      font-family="system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
      font-weight="800"
      font-size="${fontSize}px"
      fill="white"
      letter-spacing="-2"
    >J</text>
  </svg>`;

  await sharp(Buffer.from(svg))
    .png()
    .toFile(path.join(OUT, `icon-${size}.png`));

  console.log(`Created icon-${size}.png`);
}

await generateIcon(192);
await generateIcon(512);
console.log("Done.");

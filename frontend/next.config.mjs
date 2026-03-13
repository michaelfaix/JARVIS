/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["react-grid-layout"],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-DNS-Prefetch-Control", value: "on" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
        ],
      },
    ];
  },
  // ---------------------------------------------------------------------------
  // Workaround: Next.js 14 persistent file-system cache causes stale CSS.
  // When source files change while the dev server is stopped, the cached CSS
  // bundle doesn't regenerate on next startup, leading to missing styles.
  // Webpack's in-memory cache avoids this entirely and is fast enough for dev.
  // ---------------------------------------------------------------------------
  webpack: (config, { dev }) => {
    if (dev) {
      config.cache = {
        type: "memory",
      };
      // Exclude test files from webpack watching to prevent HMR chunk corruption
      config.watchOptions = Object.assign({}, config.watchOptions, {
        ignored: /src[\\/]__tests__/,
      });
    }
    return config;
  },
};

export default nextConfig;

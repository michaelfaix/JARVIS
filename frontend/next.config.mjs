/** @type {import('next').NextConfig} */
const nextConfig = {
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

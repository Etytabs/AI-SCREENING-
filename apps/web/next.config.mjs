const isGitHubPages = process.env.GITHUB_PAGES === "true";

const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] || "AI-SCREENING-";

const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  ...(isGitHubPages
    ? {
        basePath: `/${repoName}`,
        assetPrefix: `/${repoName}/`,
      }
    : {}),
};

export default nextConfig;

import esbuild from "esbuild";

const watchMode = process.argv.includes("--watch");

const ctx = await esbuild.context({
  entryPoints: ["src/index.tsx"],
  outfile: "dist/index.js",
  bundle: true,
  format: "esm",
  platform: "browser",
  target: ["es2020"],
  sourcemap: true,
  external: ["react", "react-dom", "decky-frontend-lib"],
  loader: {
    ".ts": "ts",
    ".tsx": "tsx"
  }
});

if (watchMode) {
  await ctx.watch();
  console.log("Watching for frontend changes...");
} else {
  await ctx.rebuild();
  await ctx.dispose();
  console.log("Built dist/index.js");
}

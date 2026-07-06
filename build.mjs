import path from "node:path";
import autoprefixer from "autoprefixer";
import * as esbuild from "esbuild";
import { sassPlugin } from "esbuild-sass-plugin";
import postcss from "postcss";

const nodeModules = path.resolve("node_modules");
const production = process.env.NODE_ENV === "production";

await esbuild.build({
    bundle: true,
    minify: production,
    sourcemap: !production,
    legalComments: "linked",
    outdir: "core/static",
    entryPoints: {
        main: "src/scss/main.scss",
        script: "src/js/main.js",
    },
    nodePaths: [nodeModules],
    // Content-hash fonts referenced by url() in SCSS, and rewrite the url()s.
    loader: {
        ".woff2": "file",
        ".otf": "file",
    },
    assetNames: "[hash]",
    plugins: [
        sassPlugin({
            loadPaths: [nodeModules],
            async transform(source) {
                const { css } = await postcss([autoprefixer]).process(source, { from: undefined });
                return css;
            },
        }),
    ],
});

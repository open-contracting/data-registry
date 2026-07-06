import autoprefixer from "autoprefixer";
import * as esbuild from "esbuild";
import { sassPlugin } from "esbuild-sass-plugin";
import postcss from "postcss";

const production = process.env.NODE_ENV === "production";

const options = {
    entryPoints: {
        main: "src/scss/main.scss",
        script: "src/js/main.js",
    },
    bundle: true,
    outdir: "core/static",
    minify: production,
    sourcemap: !production,
    legalComments: "linked",
    logLevel: "info",
    // The "file" loader copies fonts (referenced by url() in the SCSS) to outdir under a
    // content-hashed name and rewrites the url() to point at the copy. Without it, esbuild
    // errors: "No loader is configured for .woff2 files".
    loader: {
        ".woff2": "file",
        ".otf": "file",
    },
    plugins: [
        sassPlugin({
            async transform(source) {
                const { css } = await postcss([autoprefixer]).process(source, { from: undefined });
                return css;
            },
        }),
    ],
};

if (process.argv.includes("--watch")) {
    const context = await esbuild.context(options);
    await context.watch();
    console.log("Watching for changes …");
} else {
    await esbuild.build(options);
}

// https://getbootstrap.com/docs/4.6/getting-started/webpack/#importing-precompiled-sass
// https://webpack.js.org/loaders/sass-loader/#extracts-css-into-separate-files
// https://github.com/webpack-contrib/mini-css-extract-plugin

const MiniCssExtractPlugin = require("mini-css-extract-plugin")
const path = require('path');

module.exports = {
  entry: './src/scss/main.scss',
  output: {
    path: path.join(process.cwd(), 'core', 'static')
  },
  mode: 'production',
  module: {
    rules: [
      {
        test: /\.scss$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader', 'sass-loader']
      }
    ]
  },
  plugins: [new MiniCssExtractPlugin()]
}

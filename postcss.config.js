// https://github.com/postcss/postcss/blob/main/README.md#webpack

module.exports = {
  plugins: [
    require('precss'),
    require('autoprefixer')
  ]
}

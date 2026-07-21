const base = require("./pa11y.default.js");

module.exports = {
  ...base,
  viewport: {
    width: 320,
    height: 480,
    deviceScaleFactor: 2,
    isMobile: true,
  },
};

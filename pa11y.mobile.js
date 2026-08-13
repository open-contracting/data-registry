const base = require("./pa11y.default.js");

const knownWarnings = [
  {
    // "This element has 'position: fixed'. This may require scrolling in two dimensions."
    // https://www.w3.org/WAI/WCAG21/Techniques/css/C32
    rules: ["WCAG2AA.Principle1.Guideline1_4.1_4_10.C32,C31,C33,C38,SCR34,G206"],
    selectors: ["#filters"],
  },
];

module.exports = {
  ...base,
  defaults: {
    ...base.createDefaults(knownWarnings),
    viewport: {
      width: 320,
      height: 480,
      deviceScaleFactor: 2,
      isMobile: true,
    },
  },
};

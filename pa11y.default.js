module.exports = {
  defaults: {
    ignore: [
      // The language switcher submits on <select> change. A submit <input> is only rendered via a <noscript> element.
      // https://www.w3.org/WAI/WCAG21/Techniques/html/H32
      "WCAG2AA.Principle3.Guideline3_2.3_2_2.H32.2",
    ],
  },
};

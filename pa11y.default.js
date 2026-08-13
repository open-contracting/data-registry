const strategy = process.env.PA11Y_STRATEGY;
const includeWarnings = "PA11Y_INCLUDE_WARNINGS" in process.env;
const suppressKnownWarnings = "PA11Y_SUPPRESS_KNOWN_WARNINGS" in process.env;

const knownErrors = [
  {
    // "This form does not contain a submit button."
    // https://www.w3.org/WAI/WCAG21/Techniques/html/H32
    rules: ["WCAG2AA.Principle3.Guideline3_2.3_2_2.H32.2"],
    selectors: ["header form[method='post']"],
  },
];

const knownWarnings = [
  {
    // "This element's text is placed on a background image." (the real ratio is ~15:1, #212529 on #fff)
    // https://www.w3.org/WAI/WCAG21/Techniques/general/G18
    rules: ["WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.BgImage", "color-contrast"],
    selectors: ["select.form-select"],
  },
  {
    // "This element is absolutely positioned and the background color can not be determined."
    // https://www.w3.org/WAI/WCAG21/Techniques/general/G145
    rules: ["WCAG2AA.Principle1.Guideline1_4.1_4_3.G145.Abs"],
    selectors: ["h1.visually-hidden"],
  },
  {
    // "If this selection list contains groups of related options, they should be grouped with optgroup."
    // https://www.w3.org/WAI/WCAG21/Techniques/html/H85
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H85.2"],
    selectors: ["select#country-select"],
  },
  {
    // "Heading markup should be used if this content is intended as a heading."
    // https://www.w3.org/WAI/WCAG21/Techniques/html/H42
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H42"],
    selectors: ["#license .prose"], // license description on detail page
  },
  {
    // "If this element contains a navigation section, it is recommended that it be marked up as a list."
    // https://www.w3.org/WAI/WCAG21/Techniques/html/H48
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H48"],
    selectors: [
      ".clickable .prose", // dataset description in search result
      "h1+.prose", // dataset description on detail page
      "#description .prose", // long description on detail page
      ".bg-primary-subtle .prose", // data availability on detail page
      "#access .prose", // decompression instructions on detail page
    ],
  },
];

function createDefaults(extraKnownWarnings = []) {
  const suppressions = [
    ...knownErrors,
    ...(includeWarnings && suppressKnownWarnings ? [...knownWarnings, ...extraKnownWarnings] : []),
  ];

  const withoutSelectors = suppressions.filter((suppression) => !suppression.selectors.length);
  const withSelectors = suppressions.filter((suppression) => suppression.selectors.length);

  const hideElements =
    strategy === "hideElements" ? withSelectors.flatMap((suppression) => suppression.selectors) : [];
  const ignore = [
    ...withoutSelectors.flatMap((suppression) => suppression.rules),
    ...(strategy === "ignore" ? withSelectors.flatMap((suppression) => suppression.rules) : []),
  ];

  return {
    runners: ["htmlcs", "axe"],
    levelCapWhenNeedsReview: "warning",
    includeWarnings: includeWarnings,
    ...(hideElements.length ? { hideElements: hideElements.join(", ") } : {}),
    ...(ignore.length ? { ignore: ignore } : {}),
  };
}

module.exports = {
  createDefaults,
  defaults: createDefaults(),
};

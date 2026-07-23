// In CI, PA11Y_INCLUDE_WARNINGS is set along with PA11Y_SUPPRESS_KNOWN_WARNINGS, to allow pa11y to pass.
// In development, set PA11Y_INCLUDE_WARNINGS only, to review warnings manually.
const includeWarnings = "PA11Y_INCLUDE_WARNINGS" in process.env;

// pa11y supports hiding elements or ignoring rules - but not ignoring rules for specific elements.
// So, in development, this configuration can be run using each strategy, to avoid shadowing issues.
const strategy = process.env.PA11Y_STRATEGY || "hideElements";

// Suppress false positive warnings.
const suppressKnownWarnings = "PA11Y_SUPPRESS_KNOWN_WARNINGS" in process.env;

// Suppress false positive warnings that only occur against the live site.
const suppressKnownWarningsLive = "PA11Y_SUPPRESS_KNOWN_WARNINGS_LIVE" in process.env;

const knownErrors = {
  // "This form does not contain a submit button."
  // https://www.w3.org/WAI/WCAG21/Techniques/html/H32
  rules: ["WCAG2AA.Principle3.Guideline3_2.3_2_2.H32.2"],
  selectors: ["header form[method='post']"],
};

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
];

const knownWarningsLive = [
  {
    // "Heading markup should be used if this content is intended as a heading."
    // https://www.w3.org/WAI/WCAG21/Techniques/html/H42
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H42"],
    selectors: ["#license .prose"],
  },
  {
    // "If this element contains a navigation section, it is recommended that it be marked up as a list."
    // https://www.w3.org/WAI/WCAG21/Techniques/html/H48
    rules: ["WCAG2AA.Principle1.Guideline1_3.1_3_1.H48"],
    selectors: [
      ".clickable .prose", // dataset description in search result
      "h1+.prose", // dataset description on detail page
      "#description .prose", // long description on detail page
      ".bg-primary-subtle .prose", // quality summary on detail page
      "#access .prose",
    ],
  },
];

const suppressions = [
  knownErrors,
  ...(includeWarnings
    ? [...(suppressKnownWarnings ? knownWarnings : []), ...(suppressKnownWarningsLive ? knownWarningsLive : [])]
    : []),
];

const hideElements = strategy === "hideElements" ? suppressions.flatMap((suppression) => suppression.selectors) : [];
const ignore = strategy === "ignore" ? suppressions.flatMap((suppression) => suppression.rules) : [];

module.exports = {
  defaults: {
    runners: ["htmlcs", "axe"],
    levelCapWhenNeedsReview: "warning",
    includeWarnings: includeWarnings,
    ...(hideElements.length ? { hideElements: hideElements.join(", ") } : {}),
    ...(ignore.length ? { ignore: ignore } : {}),
  },
};

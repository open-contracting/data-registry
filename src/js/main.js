/* biome-ignore lint/correctness/noUnusedImports: Bootstrap */
import Offcanvas from "bootstrap/js/dist/offcanvas";
import Tooltip from "bootstrap/js/dist/tooltip";

document.addEventListener("DOMContentLoaded", () => {
    [...document.querySelectorAll('[data-bs-toggle="tooltip"]')].map((el) => new Tooltip(el));

    // header.html
    const languageSelect = document.querySelector("select[name='language']");
    if (languageSelect) {
        languageSelect.addEventListener("change", () => {
            languageSelect.form.submit();
        });
    }

    // search.html
    const countrySelect = document.getElementById("country-select");
    if (countrySelect) {
        countrySelect.addEventListener("change", () => {
            const url = countrySelect.value;
            if (url) {
                window.location.href = url;
            }
        });
    }
});

// detail.html

function gettext(msgid) {
    if (typeof window.catalog === "undefined") {
        return msgid;
    }
    const value = window.catalog[msgid];
    if (typeof value === "undefined") {
        return msgid;
    }
    if (typeof value === "string") {
        return value;
    }
    return value[0];
}

// Toggle content.
document.querySelectorAll(".toggleable").forEach((toggleable) => {
    const toggle = document.createElement("a");
    const showMoreText = toggleable.dataset.showMore || gettext("Show more");
    const showLessText = toggleable.dataset.showLess || gettext("Show less");

    toggle.textContent = showMoreText;
    toggle.setAttribute("aria-controls", toggleable.id);
    toggle.ariaExpanded = false;
    toggle.href = "#";

    toggle.addEventListener("click", (event) => {
        event.preventDefault();
        const collapsed = toggleable.toggleAttribute("hidden");
        toggle.textContent = collapsed ? showMoreText : showLessText;
        toggle.ariaExpanded = !collapsed;

        if (typeof fathom !== "undefined" && !collapsed) {
            fathom.trackEvent(`show more ${toggleable.id}`);
        }
    });

    let insert = toggle;
    if (toggleable.previousElementSibling.tagName === "P") {
        insert = document.createElement("p");
        insert.append(toggle);
    }

    toggleable.insertAdjacentElement("beforebegin", insert);
    toggleable.setAttribute("hidden", "");
});

// Track download events.
document.querySelectorAll("a[download]").forEach((trackable) => {
    trackable.addEventListener("click", () => {
        if (typeof fathom !== "undefined") {
            fathom.trackEvent(`download ${trackable.dataset.event}`);
        }
    });
});

// Track contact events.
document.querySelectorAll("a[data-event='contact']").forEach((link) => {
    link.addEventListener("click", () => {
        if (typeof fathom !== "undefined") {
            fathom.trackEvent("contact");
        }
    });
});

// search.html

// Make search result cards clickable.
document.querySelectorAll(".clickable").forEach((clickable) => {
    clickable.addEventListener("click", (event) => {
        // Stop "See details" from triggering a second event.
        event.preventDefault();
        window.open(
            clickable.querySelector(".click").href,
            event.ctrlKey || event.metaKey || event.shiftKey ? "_blank" : "_self",
        );
    });
});

// Enable filters.
document.querySelectorAll(".filterable").forEach((filterable) => {
    const key = filterable.dataset.key;
    const method = filterable.dataset.method;
    filterable.querySelectorAll("input").forEach((input) => {
        input.addEventListener("change", () => {
            const url = new URL(window.location.href);
            const params = new URLSearchParams(url.search);
            const values = params.getAll(key);
            if (values.includes(input.value)) {
                // URLSearchParams has no method to delete a key-value pair, and set() yields "x=a,b" not "x=a&x=b".
                params.delete(key);
                values.forEach((value) => {
                    if (value !== input.value) {
                        params.append(key, value);
                    }
                });
            } else {
                params[method](key, input.value);

                if (typeof fathom !== "undefined") {
                    fathom.trackEvent(`filter ${key}`);
                }
            }
            url.search = params.toString();
            window.location.href = url.toString();
        });
    });
});

// "8. Make the button stationary." https://www.nngroup.com/articles/back-to-top/
document.querySelectorAll(".toppable, .toppable-mobile").forEach((toppable) => {
    const observer = new window.IntersectionObserver(
        (entries) => {
            entries[0].target.querySelector("a").toggleAttribute("hidden", !entries[0].isIntersecting);
        },
        {
            rootMargin: "0px 0px -80px 0px", // 5rem
        },
    );

    observer.observe(toppable);
});

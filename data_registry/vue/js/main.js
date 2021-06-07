import "babel-polyfill";
var Promise = require('es6-promise').Promise;
require('es6-promise').polyfill();

import Vue from "vue/dist/vue.js";
import VueMoment from 'vue-moment';
import axios from 'axios';

import {BootstrapVue, IconsPlugin} from 'bootstrap-vue'

Vue.use(VueMoment)
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)

const api = axios.create({
    baseURL: "/",
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken"
})

if (document.getElementById("chevron-btn-template")) {
    Vue.component("chevron-btn", {
        delimiters: ['[[', ']]'],
        template: '#chevron-btn-template',
        props: {
            up: {type: Boolean, default: false},
            right: {type: Boolean, default: false},
            down: {type: Boolean, default: false}
        },
        computed: {
            direction: function() {
                if (this.up)            return "up"
                else if (this.right)    return "right"
                else if (this.down)     return "down"
                else                    return "left"
            }
        },
        data: function() {
            return {};
        },
        methods: {
        }
    })
}

if (document.getElementById("check-icon-template")) {
    Vue.component("check-icon", {
        delimiters: ['[[', ']]'],
        template: '#check-icon-template',
        props: {
            checked: {type: [Boolean, Number, String], default: true}
        }
    })
}

if (document.getElementById("modal-template")) {
    Vue.component("modal", {
        delimiters: ['[[', ']]'],
        template: '#modal-template'
    })
}

if (document.getElementById("dropdown-template")) {
    Vue.component("dropdown", {
        delimiters: ['[[', ']]'],
        template: '#dropdown-template',
        model: {
            prop: 'selected',
            event: 'option-selected'
        },
        props: {
            options: {type: Array, default: () => []},
            selected: {default: null},
            preselectFirst: {type: Boolean, default: false},
            placeholder: {type: String, default: null},
            labelProperty: {type: String, default: "label"},
            valueProperty: {type: String, default: null},
        },
        created: function() {
            // preselect first option if needed
            if (this.selected === null && this.preselectFirst) {
                this.selectOption(this.options[0])
            }
        },
        computed: {
            selectedOption: function() {
                if (this.valueProperty && this.options) {
                    var selected = this.options.find(n => n[this.valueProperty] == this.selected)
                    return selected ? selected : null
                }

                return this.selected
            }
        },
        methods: {
            getOptionLabel: function (option) {
                if (option === null || option === undefined) {
                    return ''
                }

                if (this.labelProperty === null) {
                    return option
                }

                return Object.prototype.hasOwnProperty.call(option, this.labelProperty) ? option[this.labelProperty] : option
            },
            selectOption: function(option) {
                this.$emit('option-selected', option && this.valueProperty ? option[this.valueProperty] : option)
            },
            isOptionSelected: function(option) {
                if (this.valueProperty === null) {
                    return option == this.selected
                }

                return option[this.valueProperty] == this.selected
            }
        }
    })
}

if (document.getElementById("search_app")) {
    new Vue({
        delimiters: ["[[", "]]"],
        el: "#search_app",
        data: function() {
            return {
                countryFilter: null,
                frequencyFilter: [],
                dataFilter: [],
                busy: false,
                dateFilter: null,
                dateFrom: null,
                dateTo: null,
            }
        },
        computed: {
            alphabet: function() {
                var result = []
                for (var i = 65; i <=90; i++) {
                    result.push(String.fromCharCode(i))
                }
                return result
            },
            filter: function() {
                return {
                    country: this.countryFilter,
                    frequency: this.frequencyFilter.length ? this.frequencyFilter : null,
                    data: this.dataFilter.length ? this.dataFilter : null,
                    date: this.dateFilter ? this.dateFilter.value : null
                }
            },
            collections: function() {
                return this.collectionsData.filter(n => {
                    n.overlap_alert = false
                    n.overlap_from = n.overlap_to = null

                    var result = true

                    if (this.filter.country) {
                        var key = `country_${this.currentLanguageCode}`
                        if (n[key]) {
                            result &= n[key].toLowerCase().startsWith(this.filter.country.toLowerCase())
                        } else {
                            result &= false
                        }
                    }

                    if (this.filter.frequency) {
                        result &= this.filter.frequency.indexOf(n.update_frequency) >= 0
                    }

                    if (this.filter.data) {
                        result &= this.filter.data.reduce((r, m) => r & n[m] > 0, true)
                    }

                    if (this.filter.date) {
                        var from = this.$moment(n.date_from)
                        var to = this.$moment(n.date_to)
                        switch (this.filter.date) {
                            case "last-year":
                                result &= from.isSameOrAfter(this.$moment().subtract(1, 'years'))
                                    || to.isSameOrAfter(this.$moment().subtract(1, 'years'))
                                break
                            case "past-6-months":
                                result &= from.isSameOrAfter(this.$moment().subtract(6, 'months'))
                                    || to.isSameOrAfter(this.$moment().subtract(6, 'months'))
                                break
                            case "custom":
                                if (this.dateFrom && this.dateTo) {
                                    if (from.isSameOrBefore(this.$moment(this.dateTo)) && to.isSameOrAfter(this.$moment(this.dateFrom))) {
                                        var isFromIn = from.isAfter(this.$moment(this.dateFrom))
                                        var isToIn = to.isBefore(this.$moment(this.dateTo))
                                        if (isFromIn || isToIn) {
                                            n.overlap_alert = true
                                            n.overlap_from = isFromIn ? n.date_from : this.dateFrom
                                            n.overlap_to = isToIn ? n.date_to : this.dateTo
                                        }
                                    } else {
                                        result &= false
                                    }
                                }

                                break
                            default:
                                break
                        }
                    }

                    return result
                })
            },
            dateFilterOptions: function() {
                return DATE_FILTER_OPTIONS
            },
            collectionsData: function() {
                return COLLECTIONS
            },
            detailDateRange: function() {
                if (this.filter.date == "custom") {
                    if (this.dateFrom && this.dateTo) {
                        return `${this.$moment(this.dateFrom).format("MMM YYYY")} - ${this.$moment(this.dateTo).format("MMM YYYY")}`
                    }
                } else {
                    var found = this.dateFilterOptions.findIndex(n => n.value == this.filter.date)
                    if (found >= 0) {
                        return this.dateFilterOptions[found].label.toLowerCase()
                    }
                }

                return null
            },
            countriesWithData: function() {
                return this.collectionsData.reduce((list, n) => {
                    var key = `country_${this.currentLanguageCode}`
                    if (!n[key]) {
                        return list
                    }

                    var letter = n[key][0].toUpperCase()
                    if (!list.includes(letter)) {
                        list.push(letter)
                    }

                    return list
                }, [])
            },
            currentLanguageCode: () => CURRENT_LANGUAGE
        },
        watch: {
            detailDateRange: function() {
                localStorage.setItem("detail-date-range", this.detailDateRange)
            }
        },
        created: function() {
            localStorage.setItem("detail-date-range", this.detailDateRange)
        },
        methods: {
            setCountryFilter: function(country) {
                if (typeof country === 'undefined' || this.countryFilter == country) {
                    this.countryFilter = null
                    return
                }

                this.countryFilter = country
            }
        }
    });
}

if (document.getElementById("detail_app")) {
    new Vue({
        delimiters: ["[[", "]]"],
        el: "#detail_app",
        data: function() {
            return {
                descriptionExpanded: false,
                feedbackType: null,
                feedback: null,
                feedbackSent: false,
                jsonYear: null,
                jsonType: "full",
                jsonDownloadBusy: false
            }
        },
        computed: {
            data: function() {
                return DATA
            },
            dateRange: function() {
                return localStorage.getItem("detail-date-range")
            },
            feedbackTypeOptions: () => FEEDBACK_TYPE_OPTIONS,
            jsonYearOptions: () => JSON_YEAR_OPTIONS,
            exporterApiUrl: () => `${EXPORTER_HOST}api/`
        },
        methods: {
            submitFeedback: function() {
                api.post("send_feedback/", {
                    type: this.feedbackType,
                    text: this.feedback
                })
                .then(() => {
                    this.feedbackSent = true

                    this.feedbackType = null
                    this.feedback = null
                })
                .catch(e => console.log(e))
            },
            submitJsonDownload: function() {
                this.jsonDownloadBusy = true

                axios.post(
                    `${this.exporterApiUrl}download_export`,
                    {
                        spider: this.data.source_id,
                        job_id: this.data.active_job,
                        year: this.jsonType == "full" ? null : this.jsonYear
                    },
                    {
                        responseType: 'arraybuffer'
                    }
                )
                .then(r => {
                    var fileURL = window.URL.createObjectURL(new Blob([r.data], { type: 'application/json' }));
                    var fileLink = document.createElement('a');
                    var fileNameMatch = /filename="(?<name>[^"]+)"/.exec(r.headers["content-disposition"])
                    var fileName = fileNameMatch.groups.name

                    fileLink.href = fileURL;
                    fileLink.setAttribute('download', fileName);
                    document.body.appendChild(fileLink);

                    fileLink.click();
                    fileLink.remove()
                })
                .catch(e => console.log(e))
                .finally(() => this.jsonDownloadBusy = false)
            }
        }
    })
}

if (document.getElementById("header")) {
    new Vue({
        delimiters: ["[[", "]]"],
        el: "#header",
        data: function() {
            return {
                language: null
            }
        },
        created: function() {
            this.language = this.languages.find(n => n.code == this.currentLanguageCode)
        },
        computed: {
            currentLanguageCode: () => CURRENT_LANGUAGE,
            languages: () => LANGUAGES
        },
        methods: {
            submit: function() {
                this.$nextTick(() => this.$refs.language_form.submit())
            },
            setAndSubmit: function(lang) {
                this.language = lang
                this.submit()
            }
        }
    })
}
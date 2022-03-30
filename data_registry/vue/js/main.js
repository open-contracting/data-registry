import "babel-polyfill";
var Promise = require('es6-promise').Promise;
require('es6-promise').polyfill();
const moment = require('moment');

import Vue from "vue/dist/vue.min.js";
import axios from 'axios';
import Vuex from 'vuex'
import createPersistedState from 'vuex-persistedstate'

import {BootstrapVue, IconsPlugin} from 'bootstrap-vue'

import { CONFIG } from "./config.js"

// https://www.npmjs.com/package/vue-moment#configuration
Vue.use(require('vue-moment'), {
    moment
})
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
Vue.use(Vuex)

const api = axios.create({
    baseURL: "/",
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken"
})

const store = new Vuex.Store({
    state: {
       searchFilter: null
    },
    getters: {
        searchFilter: state => state.searchFilter
    },
    mutations: {
        setSearchFilter: function(state, filter) {
            state.searchFilter = filter
        }
    },
    actions: {
    },
    modules: {
    },
    plugins: [
        createPersistedState(),
    ]
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

if (document.getElementById("markdown-box-template")) {
    Vue.component("markdown-box", {
        delimiters: ['[[', ']]'],
        template: '#markdown-box-template',
        props: {
            tag: {type: String, default: "div"},
            content: {type: String}
        }
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
            autoWidth: {type: Boolean, default: false}
        },
        created: function() {
            // preselect first option if needed
            if (this.selected === null && this.preselectFirst) {
                this.selectOption(this.options[0])
            }
        },
        mounted: function() {
            if (this.autoWidth) {
                this.setAutoWidth()
            }
        },
        watch: {
            options: function() {
                if (this.autoWidth) {
                    this.setAutoWidth()
                }
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
            },
            setAutoWidth: function() {
                if (!this.options || !this.options.length) {
                    return
                }

                // clone list and get its width
                let elm = this.$el.querySelector("ul").cloneNode(true)
                elm.style.visibility = 'hidden'
                elm.style.display = 'block'
                document.body.appendChild(elm)

                this.$el.style.width = `${elm.offsetWidth + 32}px`

                elm.remove()
            }
        }
    })
}

if (document.getElementById("search_app")) {
    new Vue({
        store,
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
                        result &= this.filter.data.reduce((r, m) => r & n["active_job"][m] > 0, true)
                    }

                    if (this.filter.date && n.active_job != null) {
                        var from = this.$moment(n.active_job.date_from)
                        var to = this.$moment(n.active_job.date_to)
                        var filterFrom = this.$moment(this.dateFrom)
                        var filterTo = this.$moment(this.dateTo)

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
                                    if (from.isSameOrBefore(filterTo) && to.isSameOrAfter(filterFrom)) {
                                        var isFromIn = from.isAfter(filterFrom)
                                        var isToIn = to.isBefore(filterTo)
                                        if (isFromIn || isToIn) {
                                            n.overlap_alert = true
                                            n.overlap_from = isFromIn ? n.active_job.date_from : this.dateFrom
                                            n.overlap_to = isToIn ? n.active_job.date_to : this.dateTo
                                        }
                                    } else {
                                        result &= false
                                    }
                                } else if (this.dateFrom) {
                                    if (to.isBefore(filterFrom)) {
                                        return false
                                    }

                                    if (from.isAfter(filterFrom)) {
                                        n.overlap_alert = true
                                        n.overlap_from = from.toDate()
                                        n.overlap_to = n.active_job.date_to
                                    }
                                } else if (this.dateTo) {
                                    if (from.isAfter(filterTo)) {
                                        return false
                                    }

                                    if (to.isBefore(filterTo)) {
                                        n.overlap_alert = true
                                        n.overlap_from = n.active_job.date_from
                                        n.overlap_to = to.toDate()
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
            currentLanguageCode: () => CURRENT_LANGUAGE,
            searchForStorage: function() {
                return {
                    ...this.filter,
                    ...{dateFrom: this.dateFrom, dateTo: this.dateTo}
                }
            }
        },
        watch: {
            searchForStorage: function(value) {
                this.$store.commit("setSearchFilter", value)
            }
        },
        mounted: function() {
            var filter = this.$store.getters.searchFilter
            if (filter) {
                this.countryFilter = filter.country
                this.frequencyFilter = filter.frequency ? filter.frequency : []
                this.dataFilter = filter.data ? filter.data : []
                this.dateFilter = this.dateFilterOptions.find(n => n.value == filter.date)
                this.dateFrom = filter.dateFrom
                this.dateTo = filter.dateTo
            }
        },
        methods: {
            setCountryFilter: function(country) {
                if (typeof country === 'undefined' || this.countryFilter == country) {
                    this.countryFilter = null
                    return
                }

                this.countryFilter = country
            },
            goToDetail: function(collection) {
                window.location = collection.detail_url
            }
        }
    });
}

if (document.getElementById("detail_app")) {
    new Vue({
        store,
        delimiters: ["[[", "]]"],
        el: "#detail_app",
        data: function() {
            return {
                descriptionExpanded: false,
                feedbackType: null,
                feedback: null,
                feedbackSent: false,
                exportFormat: "jsonl",
                jsonYear: null,
                jsonType: "full",
                jsonDownloadBusy: false
            }
        },
        created: function() {
            this.$moment.locale(CURRENT_LANGUAGE)
        },
        computed: {
            data: function() {
                return DATA
            },
            filter: function() {
                return this.$store.getters.searchFilter
            },
            dataRange: function() {
                if (this.filter.date == "custom") {
                    return [this.filter.dateFrom, this.filter.dateTo].filter(n => !!n).join("|")
                } else {
                    return this.filter.date
                }
            },
            feedbackTypeOptions: () => FEEDBACK_TYPE_OPTIONS,
            exportOptions: () => FORMAT_OPTIONS,
            exporterApiUrl: () => CONFIG.exporterApiBaseUrl,
            activeJob: function() {
                return DATA.active_job ? DATA.active_job : {}
            }
        },
        methods: {
            goToExcelData: function() {
                var job_id = this.data.active_job.id

                var location = `/excel_data/${job_id}`
                if (this.dataRange) {
                    location += `/${this.dataRange}`
                }

                window.location = location
            },
            submitFeedback: function() {
                api.post("send_feedback/", {
                    type: this.feedbackType,
                    text: this.feedback,
                    collection: this.data.country + " " + this.data.title
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
                        year: this.jsonType == "full" ? null : this.jsonYear,
                        format: this.exportFormat
                    },
                    {
                        responseType: 'arraybuffer'
                    }
                )
                .then(r => {
                    var fileURL = window.URL.createObjectURL(new Blob([r.data], { type: 'application/gzip' }));
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
            this.$moment.locale(CURRENT_LANGUAGE)
        },
        computed: {
            currentLanguageCode: () => CURRENT_LANGUAGE,
            languages: () => LANGUAGES,
            next: function() {
                var url = window.location.pathname
                // check if url starts with language
                if (url.startsWith(`/${this.currentLanguageCode}/`)) {
                    return url.substring(3)
                }

                return url
            }
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
import "babel-polyfill";
var Promise = require('es6-promise').Promise;
require('es6-promise').polyfill();

import Vue from "vue/dist/vue.js";
import VueMoment from 'vue-moment';

import {BootstrapVue, IconsPlugin} from 'bootstrap-vue'

Vue.use(VueMoment)
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)


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
                        result &= n.country.startsWith(this.filter.country)
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
                    var letter = n.country[0]
                    if (!list.includes(letter)) {
                        list.push(letter)
                    }

                    return list
                }, [])
            }
        },
        watch: {
            detailDateRange: function() {
                localStorage.setItem("detail-date-range", this.detailDateRange)
            }
        },
        created: function() {
            this.dateFilter = this.dateFilterOptions[0]
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
                descriptionExpanded: false
            }
        },
        computed: {
            data: function() {
                return DATA
            },
            dateRange: function() {
                return localStorage.getItem("detail-date-range")
            }
        }
    })
}

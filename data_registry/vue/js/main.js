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
                    date: this.dateFilter.value
                }
            },
            collections: function() {
                return this.collectionsData.filter(n => {
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
                        n.overlap_alert = false
                        n.overlap_from = n.overlap_to = null
                        switch (this.filter.date) {
                            case "last-year":
                                result &= this.$moment(n.date_from).isSameOrAfter(this.$moment().subtract(1, 'years'))
                                    || this.$moment(n.date_to).isSameOrAfter(this.$moment().subtract(1, 'years'))
                                break
                            case "past-6-months":
                                result &= this.$moment(n.date_from).isSameOrAfter(this.$moment().subtract(6, 'months'))
                                    || this.$moment(n.date_to).isSameOrAfter(this.$moment().subtract(6, 'months'))
                                break
                            case "custom":
                                if (this.dateFrom && this.dateTo) {
                                    var isFrom = this.$moment(n.date_from).isSameOrAfter(this.$moment(this.dateFrom))
                                    var isTo = this.$moment(n.date_to).isAfter(this.$moment(this.dateFrom))
                                        && this.$moment(n.date_to).isSameOrBefore(this.$moment(this.dateTo))

                                    result &= (isFrom || isTo)

                                    n.overlap_alert = !isFrom || !isTo
                                    n.overlap_from = n.date_from > this.dateFrom ? n.date_from : this.dateFrom
                                    n.overlap_to = n.date_to < this.dateTo ? n.date_to : this.dateTo
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
            }
        },
        created: function() {
            this.dateFilter = this.dateFilterOptions[0]
        },
        methods: {
            setCountryFilter: function(country) {
                if (this.countryFilter == country) {
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
            return {}
        },
        computed: {
            data: function() {
                return DATA
            }
        }
    })
}

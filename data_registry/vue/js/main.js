import "babel-polyfill";
var Promise = require('es6-promise').Promise;
require('es6-promise').polyfill();

import axios from "axios";
import Vue from "vue/dist/vue.js";
import VueMoment from 'vue-moment';

import {BootstrapVue, IconsPlugin} from 'bootstrap-vue'

import {CONFIG} from "./config.js";

Vue.use(VueMoment)
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)

if (document.getElementById("search_app")) {
    new Vue({
        delimiters: ["[[", "]]"],
        el: "#search_app",
        data: function() {
            return {
                collectionsData: [],
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
            }
        },
        created: function() {
            this.dateFilter = this.dateFilterOptions[0]

            this.busy = true

            axios
                .get(CONFIG.apiBaseUrl + "collections/")
                .then(r => this.collectionsData = r.data)
                .catch(e => {
                    this.collectionsData = []
                    console.log(e)
                })
                .finally(() => this.busy = false)
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
import "babel-polyfill";
var Promise = require('es6-promise').Promise;
require('es6-promise').polyfill();

import axios from "axios";
import Vue from "vue/dist/vue.js";
import VueMoment from 'vue-moment'
import {CONFIG} from "./config.js";

Vue.use(VueMoment);

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
                busy: false
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

                    return result
                })
            }
        },
        created: function() {
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
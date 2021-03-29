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
                collections: []
            }
        },
        created: function() {
            axios
                .get(CONFIG.apiBaseUrl + "collections/")
                .then(r => this.collections = r.data)
                .catch(e => {
                    this.collections = []
                    console.log(e)
                })
        }
    });
}
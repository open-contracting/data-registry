import "babel-polyfill";
var Promise = require('es6-promise').Promise;
require('es6-promise').polyfill();

// import axios from "axios";
import Vue from "vue/dist/vue.js";

if (document.getElementById("search_app")) {
    new Vue({
        delimiters: ["[[", "]]"],
        el: "#search_app",
        created: function() {
            console.log("search app")
        }
    });
}
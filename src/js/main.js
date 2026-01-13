import Offcanvas from 'bootstrap/js/dist/offcanvas'
import Tooltip from 'bootstrap/js/dist/tooltip'

document.addEventListener('DOMContentLoaded', () => {
  [...document.querySelectorAll('[data-bs-toggle="tooltip"]')].map(el => new Tooltip(el))
})

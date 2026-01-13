import Offcanvas from 'bootstrap/js/dist/offcanvas'
import Tooltip from 'bootstrap/js/dist/tooltip'

document.addEventListener('DOMContentLoaded', () => {
  [...document.querySelectorAll('[data-bs-toggle="tooltip"]')].map(el => new Tooltip(el))

  // search.html
  const select = document.getElementById('country-select')
  if (select) {
    select.addEventListener('change', () => {
      const url = select.value
      if (url) {
        window.location.href = url
      }
    })
  }
})

// detail.html

function gettext (msgid) {
  if (typeof window.catalog === 'undefined') {
    return msgid
  }
  const value = window.catalog[msgid]
  if (typeof value === 'undefined') {
    return msgid
  }
  if (typeof value === 'string') {
    return value
  }
  return value[0]
}

document.querySelectorAll('.toggleable').forEach(toggleable => {
  const toggle = document.createElement('a')

  toggle.textContent = gettext('Show more')
  toggle.setAttribute('aria-controls', toggleable.id)
  toggle.ariaExpanded = false
  toggle.href = '#'

  toggle.addEventListener('click', event => {
    event.preventDefault()
    const collapsed = toggleable.toggleAttribute('hidden')
    toggle.textContent = collapsed ? gettext('Show more') : gettext('Show less')
    toggle.ariaExpanded = !collapsed
  })

  let insert = toggle
  if (toggleable.previousElementSibling.tagName === 'P') {
    insert = document.createElement('p')
    insert.append(toggle)
  }

  toggleable.insertAdjacentElement('beforebegin', insert)
  toggleable.setAttribute('hidden', '')
})

document.querySelectorAll('a[download]').forEach(trackable => {
  if (typeof fathom !== 'undefined') {
    trackable.addEventListener('click', event => {
      fathom.trackEvent(`download ${trackable.dataset.event}`) // eslint-disable-line no-undef
    })
  }
})

// search.html

document.querySelectorAll('.clickable').forEach(div => {
  div.addEventListener('click', event => {
    // Stop "See details" from triggering a second event.
    event.preventDefault()
    window.open(div.querySelector('.click').href, event.ctrlKey || event.metaKey || event.shiftKey ? '_blank' : '_self')
  })
})

document.querySelectorAll('.filterable').forEach(filter => {
  const key = filter.dataset.key
  const method = filter.dataset.method
  filter.querySelectorAll('input').forEach(input => {
    input.addEventListener('change', event => {
      const url = new URL(window.location.href)
      const params = new URLSearchParams(url.search)
      const values = params.getAll(key)
      if (values.includes(input.value)) {
        // URLSearchParams has no method to delete a key-value pair, and set() yields "x=a,b" not "x=a&x=b".
        params.delete(key)
        values.forEach(value => {
          if (value !== input.value) {
            params.append(key, value)
          }
        })
      } else {
        params[method](key, input.value)
      }
      url.search = params.toString()
      window.location.href = url.toString()
    })
  })
})

const toppable = document.querySelector('.toppable')
if (toppable) {
  // "8. Make the button stationary." https://www.nngroup.com/articles/back-to-top/
  const observer = new window.IntersectionObserver(entries => {
    entries[0].target.querySelector('a').toggleAttribute('hidden', !entries[0].isIntersecting)
  }, {
    rootMargin: '0px 0px -80px 0px' // 5rem
  })

  observer.observe(toppable)
}

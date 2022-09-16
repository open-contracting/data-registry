document.querySelectorAll('.toggleable').forEach(toggleable => {
    const toggle = document.createElement('a')

    toggle.textContent = gettext('Show more')
    toggle.href = '#'

    toggle.addEventListener('click', event => {
        event.preventDefault()
        toggleable.toggleAttribute('hidden')
        toggle.textContent = toggleable.hasAttribute('hidden') ? gettext('Show more') : gettext('Show less')
    })

    let insert = toggle;
    if (toggleable.previousElementSibling.tagName == "P") {
        insert = document.createElement('p')
        insert.append(toggle)
    }

    toggleable.insertAdjacentElement('beforebegin', insert)
    toggleable.setAttribute('hidden', '')
})

document.querySelectorAll('.filterable').forEach(filter => {
    const key = filter.dataset.key
    const method = filter.dataset.method
    filter.querySelectorAll('input').forEach(input => {
        input.addEventListener('change', event => {
            let url = new URL(window.location.href)
            let params = new URLSearchParams(url.search)
            let values = params.getAll(key)
            if (values.includes(input.value)) {
                // URLSearchParams has no method to delete a key-value pair, and set() yields "x=a,b" not "x=a&x=b".
                params.delete(key)
                values.forEach(value => {
                    if (value != input.value) {
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

document.querySelectorAll('.clickable').forEach(div => {
    div.addEventListener('click', event => {
        window.location.href = div.querySelector('.click').href
    })
})

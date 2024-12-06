document.addEventListener('DOMContentLoaded', event => {
  const md = markdownit()

  document.querySelectorAll('.markdownable').forEach(markdownable => {
    const textarea = markdownable.querySelector('textarea')
    const preview = markdownable.querySelector('.markdownable-preview')

    textarea.addEventListener('input', event => {
      // https://til.simonwillison.net/css/resizing-textarea
      textarea.parentNode.dataset.replicatedValue = textarea.value
      // Can use timeout if performance issues.
      preview.innerHTML = md.render(textarea.value)
    })
  })

  // https://til.simonwillison.net/css/resizing-textarea
  document.querySelectorAll('textarea').forEach(textarea => {
    textarea.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }))
  })
})

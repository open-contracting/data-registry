document.addEventListener('DOMContentLoaded', event => {
  const md = markdownit()

  document.querySelectorAll('.markdownable').forEach(markdownable => {
    const textarea = markdownable.querySelector('textarea')
    const preview = markdownable.querySelector('.markdownable-preview')

    const renderMarkdown = function () {
      preview.innerHTML = md.render(textarea.value)
    }

    textarea.addEventListener('input', event => {
      // https://til.simonwillison.net/css/resizing-textarea
      textarea.parentNode.dataset.replicatedValue = textarea.value
      // Can use timeout if performance issues.
      renderMarkdown()
    })

    renderMarkdown()
  })

  // https://til.simonwillison.net/css/resizing-textarea
  document.querySelectorAll('textarea').forEach(textarea => {
    textarea.dispatchEvent(new Event('input', {bubbles: true, cancelable: true}))
  })
})

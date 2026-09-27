document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    const block = document.getElementById(button.dataset.copy);
    const text = block.textContent;
    let copied = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        copied = true;
      } else {
        const input = document.createElement('textarea');
        input.value = text;
        input.style.cssText = 'position:fixed;left:-9999px;top:0';
        document.body.append(input);
        input.select();
        copied = document.execCommand('copy');
        input.remove();
        button.focus();
      }
    } catch (_) {}
    if (!copied) {
      const range = document.createRange();
      range.selectNodeContents(block);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    button.textContent = copied ? 'Copied ✓' : 'Select & copy';
    document.getElementById('copy-status').textContent = copied ? 'Commands copied to clipboard.' : 'Commands selected. Press Control+C or Command+C to copy.';
    window.setTimeout(() => { button.textContent = 'Copy'; }, 2400);
  });
});

// Reveal setup instructions when following a direct link to either machine.
function revealSetup() {
  const target = document.getElementById(location.hash.slice(1));
  if (target && target.matches('details')) target.open = true;
}
window.addEventListener('hashchange', revealSetup);
revealSetup();

(() => {
  'use strict';

  const section = document.querySelector('[data-official-share]');
  if (!section) return;

  const status = section.querySelector('[data-copy-status]');
  if (!status) return;

  section.querySelectorAll('[data-copy-target]').forEach((button) => {
    const field = document.getElementById(button.dataset.copyTarget);
    if (!field || !section.contains(field)) return;

    button.hidden = false;
    button.addEventListener('click', async () => {
      button.disabled = true;
      status.textContent = '';

      try {
        if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
          throw new Error('Clipboard unavailable');
        }

        await navigator.clipboard.writeText(field.value);
        status.textContent = `${button.dataset.copyLabel} 복사가 완료되었습니다.`;
      } catch {
        field.focus();
        field.select();
        field.setSelectionRange(0, field.value.length);
        status.textContent = '자동 복사가 지원되지 않거나 허용되지 않았습니다. 선택된 내용을 직접 복사해 주세요.';
      } finally {
        button.disabled = false;
      }
    });
  });
})();

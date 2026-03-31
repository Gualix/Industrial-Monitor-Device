function createButton(label, className = '') {
  const button = document.createElement('button');
  button.className = `keypad-button ${className}`.trim();
  button.textContent = label;
  return button;
}

export function openKeypadModal() {
  return new Promise((resolve) => {
    const root = document.getElementById('modalRoot');
    let value = '';

    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';

    const panel = document.createElement('div');
    panel.className = 'modal-panel';

    const title = document.createElement('h2');
    title.textContent = 'Maintenance Password';

    const message = document.createElement('p');
    message.className = 'message';
    message.textContent = 'Enter the numeric password to continue.';

    const display = document.createElement('div');
    display.className = 'keypad-display';

    const grid = document.createElement('div');
    grid.className = 'keypad-grid';

    const updateDisplay = () => {
      display.textContent = value ? value.replace(/./g, '•') : '';
    };

    for (const key of ['1','2','3','4','5','6','7','8','9']) {
      const button = createButton(key);
      button.addEventListener('click', () => {
        value += key;
        updateDisplay();
      });
      grid.appendChild(button);
    }

    const clearButton = createButton('C', 'danger');
    clearButton.addEventListener('click', () => {
      value = '';
      updateDisplay();
    });

    const zeroButton = createButton('0');
    zeroButton.addEventListener('click', () => {
      value += '0';
      updateDisplay();
    });

    const okButton = createButton('OK', 'action');
    okButton.addEventListener('click', () => {
      cleanup();
      resolve(value);
    });

    grid.append(clearButton, zeroButton, okButton);

    const cancelButton = document.createElement('button');
    cancelButton.className = 'action-button';
    cancelButton.textContent = 'Cancel';
    cancelButton.style.background = '#2a3443';
    cancelButton.style.color = 'var(--text)';
    cancelButton.addEventListener('click', () => {
      cleanup();
      resolve(null);
    });

    panel.append(title, message, display, grid, cancelButton);
    backdrop.appendChild(panel);
    root.appendChild(backdrop);
    updateDisplay();

    function cleanup() {
      backdrop.remove();
    }
  });
}

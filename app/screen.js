(function () {
  'use strict';

  var dock = document.querySelector('.dock');
  var status = document.querySelector('.status');
  var active = 0;
  var pending = null;
  var buttons = window.quietFrameShortcuts.map(createShortcut);

  function createShortcut(shortcut, index) {
    var button = document.createElement('button');
    var icon = document.createElement('img');
    button.className = 'shortcut';
    button.type = 'button';
    button.tabIndex = -1;
    button.setAttribute('aria-label', 'Open ' + shortcut.label);
    button.title = shortcut.label;
    icon.src = shortcut.icon;
    icon.alt = '';
    button.appendChild(icon);
    dock.appendChild(button);
    button.addEventListener('focus', function () {
      active = index;
    });
    button.addEventListener('click', function () {
      launch(shortcut);
    });
    return button;
  }

  function focusShortcut(index) {
    if (buttons.length) {
      var button = buttons[Math.max(0, Math.min(index, buttons.length - 1))];
      button.focus();
    }
  }

  function cancelLaunch() {
    clearTimeout(pending);
    pending = null;
  }

  function launch(shortcut) {
    if (pending !== null) return;

    var platform = window.tizen;
    if (!platform) {
      status.textContent = 'TV preview. Open ' + shortcut.label + ' on your Samsung TV.';
      return;
    }

    function finish(message) {
      if (pending !== attempt) return;
      cancelLaunch();
      status.textContent = message;
    }

    function fallback() {
      finish('Open ' + shortcut.label + ' from Samsung Home.');
    }

    status.textContent = 'Opening ' + shortcut.label + '…';
    var attempt = setTimeout(fallback, 5000);
    pending = attempt;

    try {
      // A targeted, standard Tizen App Control. The TV decides whether the
      // installed target may be opened. Some consumer builds restrict this.
      var control = new platform.ApplicationControl('http://tizen.org/appcontrol/operation/default');
      platform.application.launchAppControl(control, shortcut.appId, function () {
        finish('');
      }, fallback);
    } catch (error) {
      fallback();
    }
  }

  function back() {
    cancelLaunch();
    if (status.textContent) {
      status.textContent = '';
      return;
    }
    if (window.tizen) {
      window.tizen.application.getCurrentApplication().exit();
    }
  }

  var remoteKeys = {
    13: 'Enter', 37: 'ArrowLeft', 38: 'ArrowUp', 39: 'ArrowRight',
    40: 'ArrowDown', 10009: 'Back'
  };

  document.addEventListener('keydown', function (event) {
    var key = remoteKeys[event.keyCode] || event.key;
    switch (key) {
      case 'ArrowLeft':
      case 'ArrowRight':
        event.preventDefault();
        focusShortcut(active + (key === 'ArrowLeft' ? -1 : 1));
        break;
      case 'ArrowUp':
      case 'ArrowDown':
        event.preventDefault();
        focusShortcut(active);
        break;
      case 'Enter':
        event.preventDefault();
        if (!event.repeat && buttons[active]) buttons[active].click();
        break;
      case 'Escape':
      case 'Back':
      case 'BrowserBack':
        event.preventDefault();
        if (!event.repeat) back();
        break;
    }
  });

  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) {
      cancelLaunch();
      status.textContent = '';
      focusShortcut(active);
    }
  });

  if (buttons.length) {
    // Keep the dock reachable with a keyboard in addition to remote arrows.
    dock.addEventListener('focusin', function (event) {
      buttons.forEach(function (button) {
        button.tabIndex = button === event.target ? 0 : -1;
      });
    });
    buttons[0].tabIndex = 0;
    focusShortcut(0);
  } else {
    dock.hidden = true;
  }
}());

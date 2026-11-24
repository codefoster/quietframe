(function () {
  'use strict';

  var dock = document.querySelector('.dock');
  var status = document.querySelector('.status');
  var clock = document.querySelector('.clock');
  var calendar = document.querySelector('.calendar');
  var artwork = document.querySelector('.artwork');
  var gallery = window.quietFrameGallery || [];
  var fallbackArt = artwork.getAttribute('src');
  var fallbackAlt = artwork.alt;
  var displayDay;
  var active = 0;
  var pending = null;
  var clockTimer;
  var shortcuts = window.quietFrameShortcuts;
  var buttons = shortcuts.map(createShortcut);

  function createShortcut(shortcut, index) {
    var button = document.createElement('button');
    var fallback = document.createElement('span');
    button.className = 'shortcut';
    button.type = 'button';
    button.tabIndex = -1;
    button.setAttribute('aria-label', 'Open ' + shortcut.label);
    button.title = shortcut.label;
    fallback.className = 'shortcut-fallback';
    fallback.setAttribute('aria-hidden', 'true');
    fallback.textContent = shortcut.initials || shortcut.label.slice(0, 2);
    button.appendChild(fallback);

    if (shortcut.icon) {
      var icon = document.createElement('img');
      icon.alt = '';
      icon.addEventListener('load', function () {
        icon.hidden = false;
        fallback.hidden = true;
      });
      icon.hidden = true;
      icon.src = shortcut.icon;
      button.appendChild(icon);
    }

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
      buttons[Math.max(0, Math.min(index, buttons.length - 1))].focus();
    }
  }

  function showDailyArtwork(now) {
    if (!gallery.length) return;

    // Turn the device's civil date into an ordinal without counting elapsed local hours.
    var day = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) / 86400000;
    if (day === displayDay) return;

    displayDay = day;
    var index = ((day % gallery.length) + gallery.length) % gallery.length;
    var work = gallery[index];
    var image = new Image();

    image.onload = function () {
      if (displayDay !== day) return;
      artwork.alt = work.title + ' by ' + work.artist;
      artwork.src = work.src;
    };

    image.onerror = function () {
      if (displayDay !== day) return;
      artwork.alt = fallbackAlt;
      artwork.src = fallbackArt;
    };

    image.src = work.src;
  }

  function refreshClock() {
    clearTimeout(clockTimer);
    var now = new Date();
    showDailyArtwork(now);
    clock.textContent = now.toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'});
    calendar.textContent = now.toLocaleDateString(undefined, {
      weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'
    });
    clock.dateTime = calendar.dateTime = now.toISOString();
    clockTimer = setTimeout(refreshClock, 60000 - (now.getTime() % 60000));
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
    if (document.hidden) {
      clearTimeout(clockTimer);
      return;
    }
    refreshClock();
    cancelLaunch();
    status.textContent = '';
    focusShortcut(active);
  });

  refreshClock();
  if (buttons.length) {
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

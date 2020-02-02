// ==UserScript==
// @name        neettv user script
// @namespace   neettv
// @match       http://localhost:5000/*
// @match       https://neettv.rje.li/*
// @match       http*://*.youtube.com/*
// @noframes
// @grant       GM_xmlhttpRequest
// @require     https://cdnjs.cloudflare.com/ajax/libs/pako/1.0.10/pako_deflate.min.js
// @version     0.0.1
// @author      rjeli
// ==/UserScript==

const VERSION = [0,0,1];
const BACKEND = 'http://localhost:5000';

log('starting', window.origin);

/*
const mutcfg = { attributes: true, childList: true, subtree: true };
const mutcb = (muts, obs) => {
  log('got muts:', muts);
};
const mutobs = new MutationObserver(mutcb);
mutobs.observe(document.querySelector('#masthead-container'), mutcfg);
*/

switch (window.location.host) {
case 'www.youtube.com':
  log('starting youtube scrobbler');
  startYtScrobbler();
  break;
default:
  log('doing nothing');
}

// YOUTUBE SCROBBLER

async function startYtScrobbler() {
  injectXhrProxy();
  let sentInitialData = false;
  for (;;) {
    const btns = document.querySelector('#buttons');
    if (btns && btns.children.length > 0) {
      if (btns.children[0].dataset.isScrobbler !== 'true') {
        btns.prepend(createScrobbleEl());
        log('inserted');
      }
    }
    if (!sentInitialData && unsafeWindow.ytInitialData) {
      log('initialData:', unsafeWindow.ytInitialData);
      /*
      log('watchEndpoint:', unsafeWindow.ytInitialData.currentVideoEndpoint.watchEndpoint.videoId);
      const r = unsafeWindow.ytInitialData.contents.twoColumnWatchNextResults;
      log('title:', r.results.results.contents[0].videoPrimaryInfoRenderer.title.runs[0].text);
      */
      compressAndUpload({ type: 'yt-initial-data', payload: JSON.stringify(unsafeWindow.ytInitialData) });
      sentInitialData = true;
    }
    await sleep(100);
  }
}

function injectXhrProxy() {
  const realOpen = unsafeWindow.XMLHttpRequest.prototype.open;
  unsafeWindow.XMLHttpRequest.prototype.open = function() {
    const url = arguments[1];
    if (url.startsWith('https://www.youtube.com/watch')) {
      log('proxying watch xhr', url);
      this.addEventListener('load', () => {
        log('loaded watch xhr', url, this.responseText.length);
        compressAndUpload({ type: 'yt-watch-xhr', payload: this.responseText });
      });
    }
    realOpen.apply(this, arguments);
  };
}

function createScrobbleEl() {
  const el = document.createElement('div');
  el.dataset.isScrobbler = 'true';
  el.style.background = '#070b34';
  el.style.marginTop = 'auto';
  el.style.marginBottom = 'auto';
  el.style.fontSize = '16px';
  el.style.borderRadius = '5px';
  el.style.padding = '2px 2px';
  const label = document.createElement('span');
  label.style.color = 'yellow';
  label.innerHTML = 'scrobbling...';
  el.appendChild(label);
  const chk = document.createElement('input');
  chk.type = 'checkbox';
  el.appendChild(chk);
  const link = document.createElement('a');
  link.style.color = 'white';
  link.href = 'https://neettv.rje.li';
  link.target = '_blank';
  link.innerHTML = '🡕';
  el.appendChild(link);
  return el;
}

// SEARCH SIDECAR

/*
window.addEventListener('message', evt => {
  log('got message:', evt);
  if (evt.origin !== window.origin) return;
  if (evt.data.neettvsidecar === undefined) return;
  switch (evt.data.type) {
  case 'ping':
    log('ponging');
    postMsg({ type: 'pong', version: VERSION });
    break;
  case 'search':
    search(evt.data)
      .then(results => postMsg({ type: 'searchResults', results }))
      .catch(err => {
        console.log('%cyt scraper error: %s',
          'background: red; color: white; display: block;', err);
      });
    break;
  default:
    log('unknown message type:', evt.data.type);
  }
});
*/

async function search(msg) {
  const results = {};
  if (msg.sources.includes('youtube')) {
    const ytToken = await getYtToken();
    const ytResults = await fetchYtSearchResults(ytToken, msg.query);
    results.youtube = ytResults;
  }
  return results;
}

async function getYtToken() {
  let cached = window.localStorage.getItem('ytToken');
  if (cached !== null) {
    log('using cached yt token');
    return cached;
  }
  log('fetching yt token');
  let homePage = await gmHttpRequest({
    url: 'https://www.youtube.com',
    method: 'GET',
  });
  const token = homePage.responseText.match(/"ID_TOKEN":"([^"]*)"/)[1];
  localStorage.setItem('ytToken', token);
  return token;
}

async function fetchYtSearchResults(token, query) {
  log('fetching search results');
  const encodedQuery = query.split(' ').join('+');
  let resp = await gmHttpRequest({
    url: 'https://www.youtube.com/results?search_query='+encodedQuery+'&pbj=1',
    method: 'GET',
    headers: {
      "X-YouTube-Client-Name": "1",
      "X-YouTube-Client-Version": "2.20200114.03.00",
      "X-Youtube-Identity-Token": token,
    },
  });
  return JSON.parse(resp.response);
}

// Utility functions

function log() {
  const prefix = ['%cneettv:', 'background: green; color: white;'];
  console.log.apply(null, prefix.concat(Array.from(arguments)));
}

async function gmXhr(opts) {
  return new Promise((res, rej) => {
    GM_xmlhttpRequest(Object.assign({}, opts, {
      onload: evt => res(evt),
      onerror: evt => rej(evt),
    }));
  });
}

async function compressAndUpload(data) {
  const enc = new TextEncoder();
  const utf8 = enc.encode(data.payload);
  const gzipped = pako.gzip(utf8, { level: 9 });
  const blob = new Blob([gzipped], { type: 'application/octet-stream' });
  const fd = new FormData();
  fd.append('location', window.location);
  fd.append('type', data.type);
  fd.append('payload', blob);
  await gmXhr({
    url: BACKEND+'/api/upload',
    method: 'POST',
    data: fd,
  });
  log('compressAndUpload done');
}

function waitForSelector(sel) {
  return new Promise((res, rej) => {
    innerWait(sel, 200);
    function innerWait(sel, time) {
      const el = document.querySelector(sel);
      if (el !== null) {
        res(el);
      } else {
        setTimeout(() => innerWait(sel, time), time);
      }
    };
  });
}

function waitUntil(test) {
  return new Promise((res, rej) => {
    innerWait();
    function innerWait() {
      if (test()) {
        res();
      } else {
        setTimeout(() => innerWait(), 200);
      }
    }
  });
}

function sleep(ms) {
  return new Promise((res, rej) => {
    setTimeout(() => res(), ms);
  });
}

function postMsg(msg) {
  window.postMessage({ neettvsidecar: true, ...msg });
}



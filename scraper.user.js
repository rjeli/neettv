// ==UserScript==
// @name        Yt scraper
// @namespace   Violentmonkey Scripts
// @match       file:///*
// @match       http://localhost:8000/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description 1/14/2020, 4:13:04 PM
// ==/UserScript==

function log() {
  const prefix = ['%cScraper:', 'background: green; color: white;'];
  console.log.apply(null, prefix.concat(Array.from(arguments)));
}

log('running yt scraper', window.origin);

window.addEventListener('message', evt => {
  log('got message:', evt);
});

(async function() {
  const token = await getToken();
  log('got yt token:', token);
  const searchResults = await fetchSearchResults(token);
  log('got search results:', searchResults);
  const msg = { 
    from: 'monkey', 
    type: 'yt-search-results', 
    payload: searchResults,
  };
  window.postMessage(msg, window.origin);
  log('done!');
})().catch(err => {
  console.log('%cyt scraper error: %s', 
    'background: red; color: white; display: block;', err);
});

async function getToken() {
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
  localStorage.setItem('yt-token', token);
  return token;
}

async function fetchSearchResults(token) {
  log('fetching search results');
  let resp = await gmHttpRequest({
    url: 'https://www.youtube.com/results?search_query=mobileye+bagool&pbj=1',
    method: 'GET',
    headers: {
      "X-YouTube-Client-Name": "1",
      "X-YouTube-Client-Version": "2.20200114.03.00",
      "X-Youtube-Identity-Token": token,
    },
  });
  return resp.response;
}

async function gmHttpRequest(opts) {
  return new Promise((res, rej) => {
    GM_xmlhttpRequest(Object.assign({}, opts, {
      onload: evt => res(evt),
      onerror: evt => rej(evt), 
    }));
  });
}

function genGuid() {
  let s = '';
  for (let i = 0; i < 32; i++) {
    s += Math.floor(Math.random()*16).toString(16).toLowerCase();
  }
  return s;
}

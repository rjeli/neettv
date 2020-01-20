// ==UserScript==
// @name        neettv sidecar
// @match       http://localhost:5000/*
// @match       https://neettv.rje.li/*
// @grant       GM_xmlhttpRequest
// @version     0.0.1
// @author      rjeli
// ==/UserScript==

const VERSION = [0,0,1];

function log() {
  const prefix = ['%cneettv sidecar:', 'background: green; color: white;'];
  console.log.apply(null, prefix.concat(Array.from(arguments)));
}
function postMsg(msg) {
  window.postMessage({ neettvsidecar: true, ...msg });
}
async function gmHttpRequest(opts) {
  return new Promise((res, rej) => {
    GM_xmlhttpRequest(Object.assign({}, opts, {
      onload: evt => res(evt),
      onerror: evt => rej(evt),
    }));
  });
}

log('starting', window.origin);

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

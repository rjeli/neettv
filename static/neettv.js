console.log('neettv')

const LATEST_VERSION = [0,0,1];

function postMsg(msg) {
  window.postMessage({ neettvsidecar: true, ...msg });
}

window.addEventListener('message', evt => {
  console.log('got message:', evt);
  if (evt.origin !== window.origin) return;
  if (evt.data.neettvsidecar === undefined) return;
  switch (evt.data.type) {
  case 'pong':
    console.log('got pong', evt.data.version);
    clearInterval(pinger);
    const version = evt.data.version;
    const statusEl = document.getElementById('sidecar-status');
    statusEl.innerHTML = 'sidecar found!';
    statusEl.style.color = 'palegreen';
  default:
    console.log('unknown message type:', evt.data.type);
  }
});

const pinger = setInterval(() => {
  postMsg({ type: 'ping' });
}, 1000);

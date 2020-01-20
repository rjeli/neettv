function searchButton() {
  postMsg({
    type: 'search',
    sources: ['youtube'],
    query: document.getElementById('searchquery').value,
  });
  const el = document.getElementById('searchresults');
  el.innerHTML = 'searching...';
}

window.addEventListener('message', evt => {
  console.log('got message:', evt);
  if (evt.origin !== window.origin) return;
  if (evt.data.neettvsidecar === undefined) return;
  switch (evt.data.type) {
  case 'searchResults':
    sendSearchResults(evt.data.results);
    const el = document.getElementById('searchresults');
    el.innerHTML = '';

    const ytResponse = evt.data.results.youtube[1].response;
    console.log('ytResponse:', ytResponse);

    const numResultsEl = document.createElement('p');
    numResultsEl.innerHTML = 'estimated results: ' + ytResponse.estimatedResults;
    el.appendChild(numResultsEl);

    const refinementsEl = document.createElement('p');
    refinementsEl.innerHTML = 'refinements:';
    for (let ref of ytResponse.refinements) {
      const refEl = document.createElement('a');
      refEl.href = '#';
      refEl.innerHTML = ref;
      refEl.style = 'margin-left: 10px;';
      refinementsEl.appendChild(refEl);
    }
    el.appendChild(refinementsEl);

    const resultsList = ytResponse
      .contents.twoColumnSearchResultsRenderer.primaryContents
      .sectionListRenderer.contents[0].itemSectionRenderer.contents;
    console.log('rs:', resultsList);
    const resultsListEl = document.createElement('ul');
    for (let r of resultsList) {
      const resEl = document.createElement('li');
      if (r.videoRenderer !== undefined) {
        const vr = r.videoRenderer;
        resEl.innerHTML += vr.title.runs[0].text + ' ';
        resEl.innerHTML += vr.lengthText.simpleText;
      }
      resultsListEl.appendChild(resEl);
    }
    el.appendChild(resultsListEl);

    break;
  }
});

async function sendSearchResults(results) {
  await fetch('/savesearch', {
    method: 'POST',
    body: JSON.stringify(results),
  });
  console.log('saved search');
}

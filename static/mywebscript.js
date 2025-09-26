function RunSentimentAnalysis() {
  const textToAnalyze = document.getElementById("textToAnalyze").value;

  const xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    if (this.readyState === 4 && this.status === 200) {
      const box = document.getElementById("system_response");
      const txt = this.responseText;

      // put result into the colored box
      box.innerHTML = txt;
      box.classList.remove("updated"); void box.offsetWidth; box.classList.add("updated");

      // optional: show dominant emotion badge
      const m = txt.match(/dominant emotion is (\w+)/i) || txt.match(/Dominant emotion:\s*(\w+)/i);
      const badge = document.getElementById("dominantBadge");
      const pill  = document.getElementById("dominantText");
      if (m && m[1]) {
        const dom = m[1].toLowerCase();
        badge.classList.remove("d-none");
        pill.textContent = m[1];
        pill.className = "badge badge-emo badge-" + dom;
      } else {
        badge.classList.add("d-none");
      }
    }
  };
  xhttp.open("POST", "/emotionDetector", true);
  xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  xhttp.send("textToAnalyze=" + encodeURIComponent(textToAnalyze));
}

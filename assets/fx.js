/* Einziger Effekt neben dem weichen Scrollen (smooth.js): Lichtstreif auf der Hauptueberschrift. Der Text bleibt sofort sichtbar.
   Aus bei reduzierter Bewegung und im Barrierefreiheits-Menue "Bewegung reduzieren". */
(function () {
  try {
    var H = document.documentElement;
    if (H.classList.contains("a11y-nomo") || (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches)) return;
    var h1 = document.querySelector("main h1, h1"); if (h1) h1.classList.add("fx-h");
  } catch (e) {}
})();

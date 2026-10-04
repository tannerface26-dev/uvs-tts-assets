/*
 * Universus.cards -> UVS TTS importer bookmarklet
 *
 * Run this on a https://universus.cards/deck/<id> page. It copies text in the
 * format accepted by the UVS TTS red and blue deck importers. Maybeboard cards
 * are intentionally omitted because the TTS importer has no maybeboard zone.
 */
(async () => {
  const clean = (value) => (value || "").replace(/\s+/g, " ").trim();

  if (
    location.hostname !== "universus.cards" ||
    !/^\/deck\/[0-9a-f-]+\/?$/i.test(location.pathname)
  ) {
    alert("Open a deck page on universus.cards, then run this bookmarklet.");
    return;
  }

  const mainHeading = [...document.querySelectorAll("h2")].find((heading) =>
    /^Mainboard\s*-\s*\d+/i.test(clean(heading.textContent)),
  );
  const deckRoot = mainHeading && mainHeading.parentElement;

  if (!deckRoot) {
    alert("The deck list is not available yet. Reload the page and try again.");
    return;
  }

  const directChild = (element, tagName) =>
    [...element.children].find((child) => child.tagName === tagName);

  const cardLine = (listItem) => {
    const image = listItem.querySelector('a[href*="/card/"] img[alt]');
    if (!image) return null;

    const name = clean(image.alt);
    const count =
      Number.parseInt(listItem.style.getPropertyValue("--count"), 10) ||
      listItem.querySelectorAll("picture").length ||
      1;
    const imageUrl = image.currentSrc || image.src || "";
    const path = new URL(imageUrl, location.href).pathname;
    const qualifier = path.match(/\/cards\/([^/]+)\/([^/.]+)\.(?:jpe?g|webp|png)$/i);

    return qualifier
      ? `${count} -${qualifier[1]}/${qualifier[2]} ${name}`
      : `${count} ${name}`;
  };

  const linesFrom = (container) =>
    [...container.querySelectorAll("li")].map(cardLine).filter(Boolean);

  const output = [];
  const startingHeading = [...document.querySelectorAll("h2")].find(
    (heading) => clean(heading.textContent) === "Starting Character",
  );

  if (startingHeading && startingHeading.parentElement) {
    const characterLines = linesFrom(startingHeading.parentElement);
    if (characterLines.length) {
      output.push("[b]Characters[/b]", ...characterLines, "");
    }
  }

  for (
    let group = mainHeading.nextElementSibling;
    group && group.tagName === "DIV";
    group = group.nextElementSibling
  ) {
    const typeHeading = directChild(group, "H3");
    if (!typeHeading) continue;

    const type = clean(typeHeading.textContent).replace(/\s*-\s*\d+\s*$/, "");
    const cardLines = linesFrom(group);
    if (cardLines.length) {
      output.push(`[b]${type}s[/b]`, ...cardLines, "");
    }
  }

  const sideboardDetails = [...deckRoot.querySelectorAll("details")].find(
    (details) => {
      const heading = details.querySelector("summary h2");
      return heading && /^Sideboard\s*-\s*\d+/i.test(clean(heading.textContent));
    },
  );

  if (sideboardDetails) {
    const sideboardLines = linesFrom(sideboardDetails);
    if (sideboardLines.length) {
      output.push("[b]Sideboard[/b]", ...sideboardLines, "");
    }
  }

  const text = output.join("\n").trim();
  if (!text) {
    alert("No cards were found on this deck page.");
    return;
  }

  let copied = false;
  try {
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch (_error) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    copied = document.execCommand("copy");
    textarea.remove();
  }

  if (copied) {
    alert("TTS deck list copied. Paste it into the UVS importer and click Import.");
  } else {
    prompt("Copy this TTS deck list:", text);
  }
})().catch((error) => alert(`Deck export failed: ${error.message}`));

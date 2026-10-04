/*
 * BuildUVS -> UVS TTS importer bookmarklet
 *
 * Run this on a https://builduvs.com/lists/<event>/<rank> page. It reads the
 * event's public deck-data JSON and copies text accepted by the UVS TTS red and
 * blue deck importers.
 */
(async () => {
  const hostname = location.hostname.replace(/^www\./i, "");
  const pageMatch = location.pathname.match(/^\/lists\/([^/]+)\/(\d+)\/?$/i);

  if (hostname !== "builduvs.com" || !pageMatch) {
    alert("Open an individual tournament deck on builduvs.com, then run this bookmarklet.");
    return;
  }

  const eventId = decodeURIComponent(pageMatch[1]);
  const standing = String(Number.parseInt(pageMatch[2], 10));
  const deckKey = `${eventId}#${standing}`;
  const response = await fetch(
    `/deck-data/locals/${encodeURIComponent(eventId)}.json`,
    { cache: "no-cache" },
  );

  if (!response.ok) {
    throw new Error(`BuildUVS deck data returned HTTP ${response.status}`);
  }

  const data = await response.json();
  const cards = data.cards && data.cards[deckKey];
  if (!Array.isArray(cards) || !cards.length) {
    alert("BuildUVS does not have card data for this tournament entry.");
    return;
  }

  const cardLine = (card) => {
    const quantity = Number.parseInt(card.qty, 10) || 1;
    const name = String(card.name || "")
      .replace(/[‘’‚‛′]/g, "'")
      .replace(/\s+/g, " ")
      .trim();
    const id = String(card.uvsId || "").trim();
    const divider = id.lastIndexOf("-");

    if (divider > 0) {
      const setId = id.slice(0, divider);
      const cardNumber = id.slice(divider + 1);
      if (/^[\w-]+$/.test(setId) && /^[\w-]+$/.test(cardNumber)) {
        return `${quantity} -${setId}/${cardNumber} ${name}`;
      }
    }

    return `${quantity} ${name}`;
  };

  const characters = cards.filter((card) => card.section === "character");
  const mainboard = cards.filter((card) => card.section === "main");
  const sideboard = cards.filter((card) => card.section === "sideboard");
  const output = [];

  if (characters.length) {
    output.push("[b]Characters[/b]", ...characters.map(cardLine), "");
  }
  if (mainboard.length) {
    output.push("[b]Mainboard[/b]", ...mainboard.map(cardLine), "");
  }
  if (sideboard.length) {
    output.push("[b]Sideboard[/b]", ...sideboard.map(cardLine), "");
  }

  const text = output.join("\n").trim();
  if (!text) {
    alert("No importable cards were found for this deck.");
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
    const total = (list) => list.reduce((sum, card) => sum + (Number(card.qty) || 0), 0);
    alert(
      `TTS deck list copied (${total(characters)} character, ` +
      `${total(mainboard)} mainboard, ${total(sideboard)} sideboard).`,
    );
  } else {
    prompt("Copy this TTS deck list:", text);
  }
})().catch((error) => alert(`Deck export failed: ${error.message}`));

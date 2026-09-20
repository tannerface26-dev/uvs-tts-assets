(() => {
    "use strict";

    if (globalThis.UVSU_CARD_ART) {
        return;
    }

    const STORAGE_KEY = "uvsu-card-art-v1";
    const IMAGE_VERSION = "20240802";
    const REMOTE_IMAGE_ORIGIN = "https://raw.githubusercontent.com";
    const REMOTE_IMAGE_BASE =
        "/tannerface26-dev/uvs-tts-assets/5a00047" +
        "5fcd59bd31e816e85135642e817d31998/alternate-art/";
    const REMOTE_IMAGE_PREFIXES = Object.freeze([
        `${REMOTE_IMAGE_BASE}official-gallery/images/`,
        `${REMOTE_IMAGE_BASE}runtime-images/`
    ]);

    const builtInVariantsByCardId = {
        "10509": Object.freeze([
            Object.freeze({
                label: "Original",
                setId: "yyhdt",
                cardNumber: "095"
            }),
            Object.freeze({
                label: "Alternate",
                setId: "bl01",
                cardNumber: "005"
            })
        ]),
        "10456": Object.freeze([
            Object.freeze({
                label: "Original",
                setId: "yyhdt",
                cardNumber: "044"
            }),
            Object.freeze({
                label: "Alternate",
                setId: "bl01",
                cardNumber: "006"
            })
        ]),
        "10554": Object.freeze([
            Object.freeze({
                label: "Original",
                setId: "yyhdt",
                cardNumber: "143"
            }),
            Object.freeze({
                label: "Alternate",
                setId: "bl01",
                cardNumber: "007"
            })
        ]),
        "10424": Object.freeze([
            Object.freeze({
                label: "Original",
                setId: "yyhdt",
                cardNumber: "009"
            }),
            Object.freeze({
                label: "Alternate",
                setId: "bl01",
                cardNumber: "008"
            })
        ]),
    };
    const remoteVariantsByCardId = globalThis.UVSU_REMOTE_CARD_ART || {};
    const variantsByCardId = Object.freeze(
        Object.fromEntries(
            [...new Set([
                ...Object.keys(builtInVariantsByCardId),
                ...Object.keys(remoteVariantsByCardId)
            ])].map((cardId) => [
                cardId,
                Object.freeze(
                    Array.from(
                        new Map(
                            [
                                ...(builtInVariantsByCardId[cardId] || []),
                                ...(remoteVariantsByCardId[cardId] || [])
                            ].map((variant) => [
                                `${variant.setId}/${variant.cardNumber}`,
                                variant
                            ])
                        ).values()
                    ).map((variant) => Object.freeze({
                        ...variant,
                        transformBack: variant.transformBack
                            ? Object.freeze({ ...variant.transformBack })
                            : undefined
                    }))
                )
            ])
        )
    );

    function getVariants(cardId) {
        return variantsByCardId[String(cardId)] || [];
    }

    function readSelections() {
        try {
            const stored = JSON.parse(
                window.localStorage.getItem(STORAGE_KEY) || "{}"
            );

            return stored && typeof stored === "object" ? stored : {};
        } catch (_) {
            return {};
        }
    }

    function getStorageId(cardId, deckId) {
        return deckId ? `${deckId}:${cardId}` : String(cardId);
    }

    function getSelection(cardId, deckId) {
        const variants = getVariants(cardId);

        if (!variants.length) {
            return null;
        }

        const selections = readSelections();
        const storageId = getStorageId(cardId, deckId);
        const selectedKey = selections[storageId];
        const exactSelection = variants.find(
            (variant) =>
                `${variant.setId}/${variant.cardNumber}` === selectedKey
        );

        if (exactSelection) {
            return exactSelection;
        }

        if (
            typeof selectedKey === "string" &&
            !selectedKey.includes("/")
        ) {
            const setMatches = variants.filter(
                (variant) => variant.setId === selectedKey
            );

            if (setMatches.length === 1) {
                const migrated = setMatches[0];
                selections[storageId] =
                    `${migrated.setId}/${migrated.cardNumber}`;

                try {
                    window.localStorage.setItem(
                        STORAGE_KEY,
                        JSON.stringify(selections)
                    );
                } catch (_) {
                    // The validated in-memory selection is still safe to use.
                }

                return migrated;
            }
        }

        return variants[0];
    }

    function select(cardId, setId, cardNumber, deckId) {
        const variants = getVariants(cardId);
        const selected = variants.find(
            (variant) =>
                variant.setId === setId &&
                variant.cardNumber === cardNumber
        );

        if (!selected) {
            return null;
        }

        const selections = readSelections();
        selections[getStorageId(cardId, deckId)] =
            `${selected.setId}/${selected.cardNumber}`;

        try {
            window.localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(selections)
            );
        } catch (_) {
            return null;
        }

        return selected;
    }

    function getImageURL(variant, size) {
        const suffixes = {
            full: "",
            preview: "-preview",
            mini: "-mini",
            micro: "-ci-micro"
        };

        if (!variant || !(size in suffixes)) {
            return null;
        }

        const remoteImageUrl = variant.imageUrls?.[size];

        if (remoteImageUrl) {
            try {
                const url = new URL(remoteImageUrl);
                const isAllowed =
                    url.origin === REMOTE_IMAGE_ORIGIN &&
                    REMOTE_IMAGE_PREFIXES.some((prefix) =>
                        url.pathname.startsWith(prefix)
                    ) &&
                    !url.username &&
                    !url.password &&
                    !url.search &&
                    !url.hash;

                return isAllowed ? url.href : null;
            } catch (_) {
                return null;
            }
        }

        return `/images/extensions/${variant.setId}/${variant.cardNumber}${suffixes[size]}.jpg?${IMAGE_VERSION}`;
    }

    globalThis.UVSU_CARD_ART = Object.freeze({
        getImageURL,
        getSelection,
        getVariants,
        select
    });
})();

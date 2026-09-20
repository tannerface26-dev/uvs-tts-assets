(() => {
    "use strict";

    /*
     * =========================================================
     * UVS ULTRA CUSTOM UI
     *
     * Security:
     * - No eval()
     * - No Function()
     * - No document.write()
     * - No remote scripts
     * - No fetched/injected HTML
     * - No innerHTML with site content
     * - Image URLs restricted to HTTPS
     * =========================================================
     */

    function init() {
        try {
            buildThreeColumnLayout();
            setupKeywordDropdown();
            setupComparePreview();

            console.log("[UVS Ultra Custom] Ready.");
        } catch (error) {
            console.error(
                "[UVS Ultra Custom] Initialization error:",
                error
            );
        }
    }


    /* =========================================================
       HELPERS
       ========================================================= */

    function createSection(id, title) {
        const section = document.createElement("section");
        section.id = id;
        section.className = "uvsu-section";

        const header = document.createElement("div");
        header.className = "uvsu-section-header";
        header.textContent = title;

        const body = document.createElement("div");
        body.className = "uvsu-section-body";

        section.appendChild(header);
        section.appendChild(body);

        return {
            section,
            body
        };
    }


    function createRow(labelText, className = "") {
        const row = document.createElement("div");

        row.className =
            "uvsu-row" +
            (className ? ` ${className}` : "");

        const label = document.createElement("div");
        label.className = "uvsu-row-label";
        label.textContent = labelText;

        const control = document.createElement("div");
        control.className = "uvsu-row-control";

        row.appendChild(label);
        row.appendChild(control);

        return {
            row,
            label,
            control
        };
    }


    function createGroup(title) {
        const group = document.createElement("div");
        group.className = "uvsu-symbol-group";

        const heading = document.createElement("div");
        heading.className = "uvsu-symbol-heading";
        heading.textContent = title;

        const content = document.createElement("div");
        content.className = "uvsu-symbol-content";

        group.appendChild(heading);
        group.appendChild(content);

        return {
            group,
            content
        };
    }


    function removeDirectBreaks(element) {
        if (!element) {
            return;
        }

        Array.from(element.children).forEach((child) => {
            if (child.tagName === "BR") {
                child.remove();
            }
        });
    }


    /* =========================================================
       THREE COLUMN SEARCH LAYOUT
       ========================================================= */

    function buildThreeColumnLayout() {
        const searchInputs =
            document.querySelector("#search_inputs");

        const searchGeneral =
            document.querySelector("#search_general");

        const searchInfos =
            document.querySelector("#search_infos");


        if (
            !searchInputs ||
            !searchGeneral ||
            !searchInfos
        ) {
            console.warn(
                "[UVS Ultra Custom] Search containers not found."
            );

            return;
        }


        if (document.querySelector("#uvsu-layout")) {
            return;
        }


        const layout =
            document.createElement("div");

        layout.id = "uvsu-layout";


        const cardSection =
            createSection(
                "uvsu-card-section",
                "Card Filters"
            );


        const resourceSection =
            createSection(
                "uvsu-resource-section",
                "Resource Symbols"
            );


        const infoSection =
            createSection(
                "uvsu-info-section",
                "Search Info"
            );


        layout.appendChild(cardSection.section);
        layout.appendChild(resourceSection.section);
        layout.appendChild(infoSection.section);

        searchInputs.prepend(layout);


        /* =====================================================
           CARD NAME
           ===================================================== */

        const nameInput =
            document.querySelector("#name");


        if (nameInput) {
            const row =
                createRow(
                    "Card name",
                    "uvsu-card-name-row"
                );


            const next =
                nameInput.nextElementSibling;


            const clearButton =
                next &&
                next.matches('input[type="button"]')
                    ? next
                    : null;


            row.control.appendChild(nameInput);


            if (clearButton) {
                clearButton.classList.add(
                    "uvsu-clear-button"
                );

                row.control.appendChild(
                    clearButton
                );
            }


            cardSection.body.appendChild(
                row.row
            );
        }


        /* =====================================================
           CARD TEXT
           ===================================================== */

        const cardTextInput =
            document.querySelector("#card_text");


        if (cardTextInput) {
            const row =
                createRow(
                    "Card text",
                    "uvsu-card-text-row"
                );


            const next =
                cardTextInput.nextElementSibling;


            const clearButton =
                next &&
                next.matches('input[type="button"]')
                    ? next
                    : null;


            row.control.appendChild(
                cardTextInput
            );


            if (clearButton) {
                clearButton.classList.add(
                    "uvsu-clear-button"
                );

                row.control.appendChild(
                    clearButton
                );
            }


            cardSection.body.appendChild(
                row.row
            );
        }


        /* =====================================================
           FORMAT
           ===================================================== */

        const formatList =
            document.querySelector(
                "#formattype_list"
            );


        if (formatList) {
            const row =
                createRow(
                    "Format",
                    "uvsu-format-row"
                );


            removeDirectBreaks(formatList);

            row.control.appendChild(
                formatList
            );

            cardSection.body.appendChild(
                row.row
            );
        }


        /* =====================================================
           TYPE
           ===================================================== */

        const cardTypeList =
            document.querySelector(
                "#cardtype_list"
            );


        if (cardTypeList) {
            const row =
                createRow(
                    "Type",
                    "uvsu-type-row"
                );


            row.control.appendChild(
                cardTypeList
            );

            cardSection.body.appendChild(
                row.row
            );
        }


        /* =====================================================
           RARITY
           ===================================================== */

        const rarityList =
            document.querySelector(
                "#rarity_list"
            );


        if (rarityList) {
            const row =
                createRow(
                    "Rarity",
                    "uvsu-rarity-row"
                );


            row.control.appendChild(
                rarityList
            );

            cardSection.body.appendChild(
                row.row
            );
        }


        /* =====================================================
           SET
           ===================================================== */

        const extension =
            document.querySelector("#extension");


        if (extension) {
            const row =
                createRow(
                    "Set",
                    "uvsu-set-row"
                );


            row.control.appendChild(
                extension
            );

            cardSection.body.appendChild(
                row.row
            );
        }


        /* =====================================================
           RESOURCE MATCH
           ===================================================== */

        const resourceMatchAll =
            document.querySelector(
                "#ressource_match_all"
            );


        const resourceMatchLabel =
            document.querySelector(
                'label[for="ressource_match_all"]'
            );


        if (resourceMatchAll) {
            const matchRow =
                document.createElement("div");

            matchRow.className =
                "uvsu-resource-match-row";


            matchRow.appendChild(
                resourceMatchAll
            );


            if (resourceMatchLabel) {
                matchRow.appendChild(
                    resourceMatchLabel
                );
            }


            resourceSection.body.appendChild(
                matchRow
            );
        }


        /* =====================================================
           RESOURCE SYMBOLS
           ===================================================== */

        const rsDiv =
            document.querySelector("#rs_div");


        if (rsDiv) {
            const group =
                createGroup("Symbols");

            group.content.appendChild(rsDiv);

            resourceSection.body.appendChild(
                group.group
            );
        }


        /* =====================================================
           ATTUNED RESOURCE SYMBOLS
           ===================================================== */

        const atrsDiv =
            document.querySelector("#atrs_div");


        if (atrsDiv) {
            const group =
                createGroup(
                    "Attuned Symbols"
                );

            group.content.appendChild(
                atrsDiv
            );

            resourceSection.body.appendChild(
                group.group
            );
        }


        /* =====================================================
           SEARCH INFO
           ===================================================== */

        buildSearchInfo(
            infoSection.body,
            searchInfos
        );


        searchGeneral.classList.add(
            "uvsu-original-container"
        );

        searchInfos.classList.add(
            "uvsu-original-container"
        );
    }


    /* =========================================================
       SEARCH INFO
       ========================================================= */

    function buildSearchInfo(
        target,
        searchInfos
    ) {

        /* CONTROL */

        const controlInputs =
            Array.from(
                searchInfos.querySelectorAll(
                    'input[name="cc[]"]'
                )
            );


        if (controlInputs.length) {
            addCheckboxRow(
                target,
                "Control",
                controlInputs,
                searchInfos
            );
        }


        /* DIFFICULTY */

        const difficulty =
            document.querySelector(
                "#difficulty"
            );


        const difficultyOperand =
            document.querySelector(
                'select[name="difficulty_operand"]'
            );


        if (
            difficulty ||
            difficultyOperand
        ) {
            const row =
                createRow("Difficulty");


            if (difficultyOperand) {
                row.control.appendChild(
                    difficultyOperand
                );
            }


            if (difficulty) {
                row.control.appendChild(
                    difficulty
                );
            }


            target.appendChild(row.row);
        }


        /* KEYWORD */

        const keywordDiv =
            document.querySelector(
                "#keyword_div"
            );


        const keywordMatchAll =
            document.querySelector(
                "#keyword_match_all"
            );


        const keywordMatchLabel =
            document.querySelector(
                'label[for="keyword_match_all"]'
            );


        if (
            keywordDiv ||
            keywordMatchAll
        ) {
            const row =
                createRow(
                    "Keyword",
                    "uvsu-keyword-row"
                );


            const controls =
                document.createElement("div");

            controls.className =
                "uvsu-keyword-controls";


            if (keywordMatchAll) {
                const match =
                    document.createElement("div");

                match.className =
                    "uvsu-keyword-match";

                match.appendChild(
                    keywordMatchAll
                );


                if (keywordMatchLabel) {
                    match.appendChild(
                        keywordMatchLabel
                    );
                }


                controls.appendChild(match);
            }


            if (keywordDiv) {
                controls.appendChild(
                    keywordDiv
                );
            }


            row.control.appendChild(
                controls
            );

            target.appendChild(row.row);
        }


        /* KEYWORD ADDITIONAL TEXT */

        const keywordText =
            document.querySelector(
                "#keyword_text"
            );


        if (keywordText) {
            const row =
                createRow(
                    "Keyword additional text",
                    "uvsu-keyword-text-row"
                );


            row.control.appendChild(
                keywordText
            );

            target.appendChild(row.row);
        }


        /* BLOCK MODIFIER */

        const bmOperand =
            document.querySelector(
                'select[name="bm_operand"]'
            );


        let blockModifier =
            document.querySelector(
                'input[name="block_modifier"], input[name="bm"]'
            );


        if (bmOperand) {
            const row =
                createRow(
                    "Block modifier"
                );


            row.control.appendChild(
                bmOperand
            );


            if (
                !blockModifier &&
                bmOperand.nextElementSibling &&
                bmOperand.nextElementSibling.matches(
                    'input[type="text"]'
                )
            ) {
                blockModifier =
                    bmOperand.nextElementSibling;
            }


            if (blockModifier) {
                row.control.appendChild(
                    blockModifier
                );
            }


            target.appendChild(row.row);
        }


        /* BLOCK ZONE */

        const blockZoneInputs =
            Array.from(
                searchInfos.querySelectorAll(
                    'input[name="block_zone[]"], input[name="bz[]"]'
                )
            );


        if (blockZoneInputs.length) {
            addCheckboxRow(
                target,
                "Block zone",
                blockZoneInputs,
                searchInfos
            );
        }


        /* ATTACK SPEED */

        addOperandTextRow(
            target,
            searchInfos,
            "Attack speed",
            [
                "speed_operand",
                "attack_speed_operand"
            ],
            [
                "speed",
                "attack_speed"
            ]
        );


        /* ATTACK DAMAGE */

        addOperandTextRow(
            target,
            searchInfos,
            "Attack damage",
            [
                "damage_operand",
                "attack_damage_operand"
            ],
            [
                "damage",
                "attack_damage"
            ]
        );


        /* ATTACK ZONE */

        const attackZoneInputs =
            Array.from(
                searchInfos.querySelectorAll(
                    'input[name="attack_zone[]"], input[name="zone[]"]'
                )
            );


        if (attackZoneInputs.length) {
            addCheckboxRow(
                target,
                "Attack zone",
                attackZoneInputs,
                searchInfos
            );
        }
    }


    /* =========================================================
       CHECKBOX ROW
       ========================================================= */

    function addCheckboxRow(
        target,
        labelText,
        inputs,
        searchInfos
    ) {
        const row =
            createRow(labelText);


        inputs.forEach((input) => {
            const item =
                document.createElement("span");

            item.className =
                "uvsu-inline-option";


            let label = null;


            if (input.id) {
                try {
                    label =
                        searchInfos.querySelector(
                            `label[for="${CSS.escape(input.id)}"]`
                        );
                } catch (_) {
                    label = null;
                }
            }


            item.appendChild(input);


            if (label) {
                item.appendChild(label);
            }


            row.control.appendChild(item);
        });


        target.appendChild(row.row);
    }


    /* =========================================================
       OPERAND + TEXT ROW
       ========================================================= */

    function addOperandTextRow(
        target,
        searchInfos,
        labelText,
        operandNames,
        inputNames
    ) {
        let operand = null;
        let input = null;


        for (const name of operandNames) {
            operand =
                searchInfos.querySelector(
                    `select[name="${name}"]`
                );

            if (operand) {
                break;
            }
        }


        for (const name of inputNames) {
            input =
                searchInfos.querySelector(
                    `input[name="${name}"]`
                );

            if (input) {
                break;
            }
        }


        if (
            operand &&
            !input &&
            operand.nextElementSibling &&
            operand.nextElementSibling.matches(
                'input[type="text"]'
            )
        ) {
            input =
                operand.nextElementSibling;
        }


        if (!operand && !input) {
            return;
        }


        const row =
            createRow(labelText);


        if (operand) {
            row.control.appendChild(
                operand
            );
        }


        if (input) {
            row.control.appendChild(
                input
            );
        }


        target.appendChild(row.row);
    }


    /* =========================================================
       KEYWORD DROPDOWN
       ========================================================= */

    function setupKeywordDropdown() {
        const keywordDiv =
            document.querySelector(
                "#keyword_div"
            );


        if (!keywordDiv) {
            return;
        }


        if (
            keywordDiv.classList.contains(
                "uvsu-keywords-ready"
            )
        ) {
            return;
        }


        const keywordRows =
            Array.from(
                keywordDiv.querySelectorAll(
                    ".float_keyword"
                )
            );


        if (!keywordRows.length) {
            return;
        }


        /*
         * Alphabetical order
         */

        keywordRows.sort((a, b) => {
            const textA =
                (
                    a.querySelector("label")
                        ?.textContent ||
                    ""
                ).trim();


            const textB =
                (
                    b.querySelector("label")
                        ?.textContent ||
                    ""
                ).trim();


            return textA.localeCompare(
                textB,
                undefined,
                {
                    sensitivity: "base"
                }
            );
        });


        const button =
            document.createElement("button");

        button.type = "button";
        button.className =
            "uvsu-keyword-button";


        const buttonText =
            document.createElement("span");

        buttonText.className =
            "uvsu-keyword-button-text";

        buttonText.textContent =
            "Select Keywords";


        button.appendChild(buttonText);


        const menu =
            document.createElement("div");

        menu.className =
            "uvsu-keyword-menu";


        /*
         * Move existing controls instead of
         * creating replacement inputs.
         */

        keywordRows.forEach((row) => {
            menu.appendChild(row);
        });


        keywordDiv.appendChild(button);
        keywordDiv.appendChild(menu);

        keywordDiv.classList.add(
            "uvsu-keywords-ready"
        );


        button.addEventListener(
            "click",
            (event) => {
                event.preventDefault();
                event.stopPropagation();

                keywordDiv.classList.toggle(
                    "uvsu-open"
                );
            }
        );


        menu.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();
            }
        );


        document.addEventListener(
            "click",
            () => {
                keywordDiv.classList.remove(
                    "uvsu-open"
                );
            }
        );


        function updateKeywordButton() {
            const checked =
                Array.from(
                    keywordDiv.querySelectorAll(
                        'input[name="keyword[]"]:checked'
                    )
                );


            if (checked.length === 0) {
                buttonText.textContent =
                    "Select Keywords";

                return;
            }


            if (checked.length === 1) {
                const row =
                    checked[0].closest(
                        ".float_keyword"
                    );


                const label =
                    row?.querySelector(
                        "label"
                    );


                const text =
                    label?.textContent
                        ?.trim();


                buttonText.textContent =
                    text ||
                    "1 Keyword Selected";

                return;
            }


            buttonText.textContent =
                `${checked.length} Keywords Selected`;
        }


        keywordDiv
            .querySelectorAll(
                'input[name="keyword[]"]'
            )
            .forEach((checkbox) => {
                checkbox.addEventListener(
                    "change",
                    updateKeywordButton
                );
            });


        updateKeywordButton();
    }


    /* =========================================================
       COMPARE PREVIEW SYSTEM
       ========================================================= */

    function setupComparePreview() {

        /* =====================================================
           CREATE LOCKED PREVIEW
           ===================================================== */

        let lockedPreview =
            document.querySelector(
                "#uvsu-locked-preview"
            );


        if (!lockedPreview) {
            lockedPreview =
                document.createElement("div");

            lockedPreview.id =
                "uvsu-locked-preview";

            lockedPreview.hidden = true;


            const lockedImage =
                document.createElement("img");

            lockedImage.id =
                "uvsu-locked-preview-image";

            lockedImage.alt =
                "Locked card preview";

            lockedImage.draggable =
                false;


            const label =
                document.createElement("div");

            label.className =
                "uvsu-locked-label";

            label.textContent =
                "LOCKED";


            lockedPreview.appendChild(
                lockedImage
            );

            lockedPreview.appendChild(
                label
            );


            document.body.appendChild(
                lockedPreview
            );
        }


        const lockedImage =
            document.querySelector(
                "#uvsu-locked-preview-image"
            );


        if (!lockedImage) {
            return;
        }


        /* =====================================================
           SAFE IMAGE URL
           ===================================================== */

        function getSafeImageURL(source) {
            if (
                typeof source !==
                "string"
            ) {
                return null;
            }


            try {
                const url =
                    new URL(
                        source,
                        window.location.href
                    );


                /*
                 * Only allow normal web resources.
                 */

                if (
                    url.protocol !== "https:"
                ) {
                    return null;
                }


                return url.href;

            } catch (_) {
                return null;
            }
        }


        /* =====================================================
           GET CURRENT HOVER IMAGE
           ===================================================== */

        function getHoverPreviewImage() {
            return document.querySelector(
                "#preview-image img"
            );
        }


        /* =====================================================
           LOCK CURRENT CARD
           ===================================================== */

        function lockCurrentPreview() {
            const hoverImage =
                getHoverPreviewImage();


            if (!hoverImage) {
                return;
            }


            const safeURL =
                getSafeImageURL(
                    hoverImage.currentSrc ||
                    hoverImage.src
                );


            if (!safeURL) {
                console.warn(
                    "[UVS Ultra Custom] Preview URL rejected."
                );

                return;
            }


            lockedImage.src =
                safeURL;

            lockedPreview.hidden =
                false;

            lockedPreview.classList.add(
                "uvsu-has-card"
            );
        }


        /* =====================================================
           CLEAR LOCKED CARD
           ===================================================== */

        function clearLockedPreview() {
            lockedPreview.hidden =
                true;

            lockedPreview.classList.remove(
                "uvsu-has-card"
            );

            lockedImage.removeAttribute(
                "src"
            );
        }


        /* =====================================================
           CLICK RESULT IMAGE -> LOCK
           ===================================================== */

        document.addEventListener(
            "click",
            (event) => {

                if (
                    !(
                        event.target
                        instanceof Element
                    )
                ) {
                    return;
                }


                const miniImage =
                    event.target.closest(
                        ".card_image img, .mini_image"
                    );


                if (!miniImage) {
                    return;
                }


                const card =
                    miniImage.closest(
                        ".card"
                    );


                const imageContainer =
                    miniImage.closest(
                        ".card_image"
                    );


                if (
                    !card ||
                    !imageContainer
                ) {
                    return;
                }


                /*
                 * Small card image click is reserved
                 * for locking the compare preview.
                 */

                event.preventDefault();

                event.stopPropagation();

                event.stopImmediatePropagation();


                /*
                 * Allow the site's normal hover preview
                 * to finish updating first.
                 */

                window.requestAnimationFrame(
                    () => {
                        lockCurrentPreview();
                    }
                );

            },
            true
        );


        /* =====================================================
           CLICK LOCKED IMAGE -> CLEAR
           ===================================================== */

        lockedPreview.addEventListener(
            "click",
            (event) => {
                event.preventDefault();
                event.stopPropagation();

                clearLockedPreview();
            }
        );


        /* =====================================================
           KEYBOARD ACCESSIBILITY
           ===================================================== */

        lockedPreview.tabIndex = 0;

        lockedPreview.setAttribute(
            "role",
            "button"
        );

        lockedPreview.setAttribute(
            "aria-label",
            "Clear locked card preview"
        );


        lockedPreview.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {
                    event.preventDefault();

                    clearLockedPreview();
                }
            }
        );


        /* =====================================================
           KEEP PREVIEWS ANCHORED
           ===================================================== */

        let fixedPreviewTop = null;

function positionPreviewSystem() {
    const content =
        document.querySelector("#content");

    if (!content) {
        return;
    }


    const rect =
        content.getBoundingClientRect();

    const rootStyles =
        getComputedStyle(
            document.documentElement
        );

    const previewWidth =
        parseFloat(
            rootStyles.getPropertyValue(
                "--uvsu-preview-width"
            )
        ) || 300;

    const previewGap =
        parseFloat(
            rootStyles.getPropertyValue(
                "--uvsu-preview-gap"
            )
        ) || 12;


    /*
     * X POSITION
     *
     * Left edge of hover preview =
     * right edge of #content.
     */
    const hoverLeft =
        rect.right;


    /*
     * Locked preview sits to the
     * right of hover preview.
     */
    const lockedLeft =
        hoverLeft +
        previewWidth +
        previewGap;


    /*
     * Y POSITION
     *
     * Capture the top of #content ONCE.
     *
     * Because the previews use position: fixed,
     * this becomes their permanent viewport Y
     * position while scrolling.
     */
    if (fixedPreviewTop === null) {
        fixedPreviewTop =
            rect.top;
    }


    document.documentElement.style.setProperty(
        "--uvsu-preview-left",
        `${hoverLeft}px`
    );

    document.documentElement.style.setProperty(
        "--uvsu-locked-left",
        `${lockedLeft}px`
    );

    document.documentElement.style.setProperty(
        "--uvsu-preview-top",
        `${fixedPreviewTop}px`
    );
}


        /*
         * Watch #content for search-result changes.
         *
         * UVS Ultra updates results dynamically, so
         * recalculate when the results DOM changes.
         */

        const content =
            document.querySelector(
                "#content"
            );


        if (content) {
            const contentObserver =
                new MutationObserver(
                    () => {
                        window.requestAnimationFrame(
                            positionPreviewSystem
                        );
                    }
                );


            contentObserver.observe(
                content,
                {
                    childList: true,
                    subtree: true
                }
            );
        }
    }


    /* =========================================================
       START
       ========================================================= */

    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            init,
            {
                once: true
            }
        );
    } else {
        init();
    }

})();

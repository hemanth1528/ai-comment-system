async function translateComment(id) {

    const response = await fetch(`/translate/${id}`);

    const data = await response.json();

    document.getElementById(`translated-${id}`).innerText =
        "Translated: " + data.translated_text;
}

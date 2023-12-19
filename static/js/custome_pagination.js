
function  addFieldToSearchForm(){
    const searchForm = document.getElementById('changelist-search');
    const modelFieldInput = document.getElementById('model-fields-form');
    searchForm.appendChild(modelFieldInput);
}

function setNextPage(isNextPage, el) {
    el = document.getElementById(el);
    const qString = new URLSearchParams(el.href)
    const pageNumber = qString.get('p')

    if (qString.get('p') != null) {
        if (!(parseInt(qString.get('p')) < 2 && !isNextPage)){
            qString.set('p', isNextPage ? (parseInt(pageNumber) + 1).toString() : (parseInt(pageNumber) - 1))
        }
    }
    else {
        qString.set('p', isNextPage?'2':'1')
    }
    el.href = decodeURIComponent(qString.toString())
}
window.addEventListener('load', () => {
    setNextPage(false, 'prevBtn');
    addFieldToSearchForm();
})
window.addEventListener('load', () => setNextPage(true, 'nextBtn'))

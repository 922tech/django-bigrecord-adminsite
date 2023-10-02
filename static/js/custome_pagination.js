const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
alert('sdsfdf')
function setNextPage() {

    console.log('setNextPage');

    const el = document.getElementById('nextBtn');
    const qString = new URLSearchParams(el.href)

    if (qString.get('q') === null) {
        return
    }

    const pageNumber = qString.get('p')

    if (qString.get('p') != null) {
        qString.set('p', (parseInt(pageNumber) + 1).toString())
        console.log(qString.get('p'))
    } else {
        qString.set('p', '2')
    }

    el.href = '//' + decodeURIComponent(q.toString())
    console.log(el.href)
}

let b = document.getElementById('btnn')
console.log(b);
b.addEventListener('onclick', setNextPage);

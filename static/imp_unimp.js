function sendimp_req(x) {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/mark-important/')

    xhr.setRequestHeader("x-csrf-token", csrftoken);
    var data = new FormData();
    data.append('id', x);
    xhr.send(data)

    document.getElementById(x + "_unimp").style.display = 'block'
    document.getElementById(x + "_imp").style.display = 'none'
}

function sendunimp_req(x) {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/mark-unimportant/')

    xhr.setRequestHeader("x-csrf-token", csrftoken);
    var data = new FormData();
    data.append('id', x);
    xhr.send(data)

    document.getElementById(x + "_unimp").style.display = 'none'
    document.getElementById(x + "_imp").style.display = 'block'
}

function send_unimpreq(x) {
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/mark-unimportant/')

    xhr.setRequestHeader("x-csrf-token", csrftoken);
    var data = new FormData();
    data.append('id', x);
    xhr.send(data);

    document.getElementById(x).remove();
    location.reload();
}


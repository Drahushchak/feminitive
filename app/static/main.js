$('input[id=upload-file]').change(function(file) {
    $('#')
});

$('input.source-checkbox').change(function(el){
        let n_selected = $('input.source-checkbox:checked').length
        let submit_b = $('#source-dashboard-submit')
        if(n_selected==0){
            submit_b.addClass('d-none')
            submit_b.removeClass('d-block')
        } else if(n_selected==1){
            submit_b.removeClass('d-none')
            submit_b.addClass('d-block')
            submit_b.val('Show Chart')
        } else {
            submit_b.removeClass('d-none')
            submit_b.addClass('d-block')
            submit_b.val('Show Comparative Chart')
        }
    }
)

if ('serviceWorker' in navigator) {
    navigator.serviceWorker
    .register('./service-worker.js')
    .then(function(registration) {
        console.log('Service Worker Registered!');
        return registration;
    })
    .catch(function(err) {
        console.error('Unable to register service worker.', err);
    });
}
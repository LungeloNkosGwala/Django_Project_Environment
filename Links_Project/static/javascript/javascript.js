$(document).ready( function () {
    $('#table').DataTable();
} );



$("button#up").click(function(){
	$("select").moveSelectedUp();
});
$("button#down").click(function(){
	$("select").moveSelectedDown();
});

$('input[type="checkbox"]').on('change', function() {
	$(this).siblings('input[type="checkbox"]').prop('checked', false);
 });
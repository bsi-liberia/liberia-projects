$("select[name='currency_disbursements'], select[name='currency_mtef']").val("USD");

$("#disbursementtemplates a").click(function(e) {
	e.preventDefault();
	var url = $(this).attr("href");
	var currency = $("select[name='currency_disbursements']").val();
	window.location.href = (url + "?currency=" + currency);
});

$("#mteftemplates a").click(function(e) {
	e.preventDefault();
	var url = $(this).attr("href");
	var currency = $("select[name='currency_mtef']").val();
	window.location.href = (url + "&currency=" + currency);
});

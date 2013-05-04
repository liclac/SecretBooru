function delete_self() {
	$.ajax({
		type: 'DELETE'
	}).done(function(data) {
		window.location = data
	})
}
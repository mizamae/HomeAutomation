$(document).ready(function(){
	
	context.init({preventDoubleContext: false});
	
	context.attach('.ms-selection', [
		{header: 'Options'},
		{text: 'Calculate mean', href: '#'},
		{text: 'Calculate max', href: '#'},
		{text: 'Calculate min', href: '#'},
		{divider: true},
		{text: 'Copy', href: '#'},
		{text: 'Dafuq!?', href: '#'}
	]);
	
	context.settings({compress: true});
	
	
	$(document).on('mouseover', '.me-codesta', function(){
		$('.finale h1:first').css({opacity:0});
		$('.finale h1:last').css({opacity:1});
	});
	
	$(document).on('mouseout', '.me-codesta', function(){
		$('.finale h1:last').css({opacity:0});
		$('.finale h1:first').css({opacity:1});
	});
	
});
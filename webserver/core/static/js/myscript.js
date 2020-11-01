$(function(){

    // Basic example
    $('.example1').click(function(){

        $.preloader.start();

        setTimeout(function(){
            $.preloader.stop();
        }, 3000);

    });

    // Advanced example
    $('.example2').click(function(){

        $.preloader.start({
            modal: true,
            src : 'sprites2.png'
        });

    });

    //$('.example2').unload(function(){
    //    $.preloader.stop();
    //});

    // With button example
    $('.example3').click(function(){

        var e = $('<div/>').css({'margin-left': '10px', 'display': 'inline-block', 'vertical-align': 'middle'}).insertAfter(this).preloader({src:'sprites.32.png'});

        setTimeout(function(){
            e.preloader('stop');
        }, 3000);

    });

});
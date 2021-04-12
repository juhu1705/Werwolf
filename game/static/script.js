function focusFunc() {
    let parent = this.parentNode.parentNode;
    parent.classList.add('focus');
}

function blurFunc() {
    let parent = this.parentNode.parentNode;
    if(this.value == "") {
        parent.classList.remove('focus');
    }
}

function setChoices() {
    const selected = document.querySelectorAll(".selected");

    selected.forEach(select => {
        arrow = select.parentNode.parentNode.parentNode.querySelector('.arrow');
        if(arrow !== null) {
            arrow.addEventListener("click", () => {
                optionContainer = select.parentNode.querySelector(".option-container");
                optionContainer.classList.toggle("active");
                arrowDown = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-down");
                arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
                if(arrowDown !== null) {
                    arrowDown.classList.remove("fa-angle-down");
                    arrowDown.classList.toggle("fa-angle-up");
                }

                if(arrowUp !== null) {
                    arrowUp.classList.toggle("fa-angle-down");
                    arrowUp.classList.remove("fa-angle-up");
                }
            });
        }

        select.addEventListener("click", () => {
            optionContainer = select.parentNode.querySelector(".option-container");
            optionContainer.classList.toggle("active");
            arrowDown = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-down");
            arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
            if(arrowDown !== null) {
                arrowDown.classList.remove("fa-angle-down");
                arrowDown.classList.toggle("fa-angle-up");
            }

            if(arrowUp !== null) {
                arrowUp.classList.toggle("fa-angle-down");
                arrowUp.classList.remove("fa-angle-up");
            }
        });

        if (!select.classList.contains('special')) {

            optionsList = select.parentNode.querySelectorAll(".option");
            optionsList.forEach( o => {
                o.addEventListener("click", () => {
                    select.value = o.querySelector("label").innerHTML;
                    optionContainer = select.parentNode.querySelector(".option-container");
                    optionContainer.classList.remove("active");
                    header = select.parentNode.parentNode.querySelector('.selection-header');
                    if(header !== null) {
                        header.classList.add('active');
                    }
                    arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
                    if(arrowUp !== null) {
                        arrowUp.classList.toggle("fa-angle-down");
                        arrowUp.classList.remove("fa-angle-up");
                    }
                    select.parentNode.parentNode.parentNode.classList.add('focus');
                });
            });

        }
        searchBox = select.parentNode.querySelector(".search-box input");
        searchBox.addEventListener("keyup", function(e) {
            var input = e.target;
            var filter = input.value.toUpperCase();
            var options = select.parentNode.querySelectorAll('.option label');
            var i;
            for(i = 0; i < options.length; i++) {
                topic = options[i];

                if(topic.innerHTML.toUpperCase().indexOf(filter)>-1) {
                    options[i].parentNode.style.display = "";
                } else {
                    options[i].parentNode.style.display = "none";
                }
            }
        });


        let parent = select.parentNode.parentNode.parentNode;

        if(parent.querySelector('.second') == null && select.value !== null && select.value !== '') {
            parent.classList.add('focus');
        }
    });
}

function upgradeOptions() {
    const selected = document.querySelectorAll(".selected");
    selected.forEach(select => {
        if (!select.classList.contains('special')) {
            optionsList = select.parentNode.querySelectorAll(".option");
            optionsList.forEach( o => {
                o.addEventListener("click", () => {
                    select.value = o.querySelector("label").innerHTML;
                    optionContainer = select.parentNode.querySelector(".option-container");
                    optionContainer.classList.remove("active");
                    header = select.parentNode.parentNode.querySelector('.selection-header');
                    if(header !== null) {
                        header.classList.add('active');
                    }
                    arrowUp = select.parentNode.parentNode.parentNode.querySelector(".fa-angle-up");
                    if(arrowUp !== null) {
                        arrowUp.classList.toggle("fa-angle-down");
                        arrowUp.classList.remove("fa-angle-up");
                    }
                    select.parentNode.parentNode.parentNode.classList.add('focus');
                });
            });
        }
    });
}

var socket = io.connect('https://' + document.domain + ":" + location.port);

$(document).ready(() => {
    $(".my_audio").trigger('load');

    socket.on('connect', () => {
        socket.send("I am connected");
        $('.rooms').addClass('hide');
        $('.action').addClass('hide');
        $('.login_action').removeClass('hide');
        $('.game-settings').addClass('hide');
        $('.continue').addClass('hide');
        $('.votes').html('');
    });

    socket.on('warn', (data) => {
        $('.flash-container').append('<div class="flash flash-error" tabindex="0">' + data + '</div>');
        $('.flash').filter(":contains('" + data + "')").on('click', () => {
            $('.flash').filter(":contains('" + data + "')").fadeOut(1000, () => {
                $('.flash').filter(":contains('" + data + "')").remove();
            });
        });
    });

    socket.on('info', (data) => {
        $('.flash-container').append('<div class="flash" tabindex="0">' + data + '</div>');
        $('.flash').filter(":contains('" + data + "')").on('click', () => {
            $('.flash').filter(":contains('" + data + "')").fadeOut(1000, () => {
                $('.flash').filter(":contains('" + data + "')").remove();
            });
        });
    });

    socket.on('message', (data) => {
        console.log(`Message: ${data}`);
    });

    socket.on('display_header', (data) => {
        console.log(`Message: ${data}`);
        $('.action_header').html(data);
    });

    socket.on('display_text', (data) => {
        console.log(`Message: ${data}`);
        $(".action_text").html('<div class="text_content">' + data + '</div>');
    });

    socket.on('append_text', (data) => {
        console.log(`Message: ${data}`);
        $(".action_text").append('<div class="text_content">' + data + '</div>');
    });

    socket.on('show_rooms', (data) => {
        console.log(`Message: Display rooms`);
        $('.rooms').removeClass('hide');
        $('.login_action').addClass('hide');
        $('.action').addClass('hide');
        $('.game-settings').addClass('hide');
        $('.continue').addClass('hide');
    });

    socket.on('show_room', (data) => {
        $('.rooms').addClass('hide');
        $('.login_action').addClass('hide');
        $('.action').addClass('hide');
        $('.continue').addClass('hide');
    });

    socket.on('correct_vote', (data) => {
        $('.rooms').addClass('hide');
        $('.login_action').addClass('hide');
        $('.continue').addClass('hide');

        $('.action').removeClass('hide');
    });

    socket.on('hide_vote', (data) => {
        $('.action').addClass('hide');
    });

    socket.on('put_choices', (data) => {
        $('.rooms').addClass('hide');
        $('.login_action').addClass('hide');
        $('.continue').addClass('hide');

        $('.choose').removeClass('focus');
        $('.choose').find('.option-container').html(data);
        $('.choose').find('#selected_player').val('');
        $('.action').removeClass('hide');

        upgradeOptions();
    });

    socket.on('request_next', (data) => {
        $('.rooms').addClass('hide');
        $('.login_action').addClass('hide');
        $('.action').addClass('hide');
        $('.continue').removeClass('hide');
    });

    socket.on('set_username', (data) => {
        console.log(`Message: ${data}`);
        $(".username").html(data);
    });

    socket.on('set_room_name', (data) => {
        console.log(`Message: ${data}`);
        $(".room_name").html(data);
    });

    socket.on('set_role', (data) => {
        console.log(`Message: ${data}`);
        $(".role_name").html(data);
        $('.game-settings').addClass('hide');
        $('.admin-only-override').addClass('hide');
    });

    socket.on('wait', (data) => {
        $('.action').addClass('hide');
        $('.continue').addClass('hide');
    });

    socket.on('set_explanation', (data) => {
        console.log(`Message: ${data}`);
        $(".explanation").html(data);
    });

    socket.on('show_settings', (data) => {
        console.log(`Message: ${data}`);
        $('.settings-header').html(data);
        $('.settings-listed').html('');
        $('.game-settings').removeClass('hide');
        $('.admin-only-override').addClass('hide');
    });

    socket.on('hide_settings', (data) => {
        $('.game-settings').addClass('hide');
    });

    socket.on('append_setting', (data) => {
        $('.settings-listed').append(data);
        $('.setting').attr('readonly', 'readonly');
    });

    socket.on('show_admin_room', (data) => {
        $('.admin-only-override').removeClass('hide');
        $('.setting').attr('readonly', false);
    });

    socket.on('display_votes', (data) => {
        $('.votes').html(data);
    });

    socket.on('set_role_img', (data) => {
        $('.role_picture').find("img").addClass('hide');
        $(data).removeClass('hide');
    });

    socket.on('hide_continue', (data) => {
        $('.continue').addClass('hide');
    });

    socket.on('hide_action', (data) => {
        $('.action').addClass('hide');
    });

    socket.on('play_sound', (data) => {
        $('.my_audio').trigger('pause');
        var audios = document.querySelectorAll(".my_audio");
        audios.forEach(audio => {
            audio.currentTime = 0;
        });
        $("#" + data).trigger('play');
    });

    socket.on('display_volume', (data) => {
        if(data == 'on') {
            $('#mute').find('i').removeClass('fa-volume-mute');
            $('#mute').find('i').addClass('fa-volume-up');
        } else {
            $('#mute').find('i').removeClass('fa-volume-up');
            $('#mute').find('i').addClass('fa-volume-mute');
        }
    });

    $('#login').on('click', () => {
        var name = $('#username').val();
        if(name == '') {
            $(".action_text").html('<div class="text_content">A username is needed</div>');
            return;
        }

        socket.emit('username', name);
        console.log(`Send: ${name}`);
    });

    $('#create').on('click', () => {
        var room_name = $('#roomname').val();
        socket.emit('create_room', room_name);
        console.log(`Send: ${room_name}`);
    });

    $('#join').on('click', () => {
        var room_name = $('#roomname').val();
        console.log(`Send: ${room_name}`);
        socket.emit('join_room', room_name);
    });

    $('#save').on('click', () => {
        var wolves_count = $('#wolves_count').val();
        var witches_count = $('#witches_count').val();
        var searchers_count = $('#searchers_count').val();
        var hunter_count = $('#hunter_count').val();
        var protector_count = $('#protector_count').val();
        var amor_count = $('#amor_count').val();

        socket.emit('room_settings', {'wolves_count': wolves_count, 'witches_count': witches_count, 'searchers_count': searchers_count,
                                        'hunter_count': hunter_count, 'protector_count': protector_count, 'amor_count': amor_count});
    });

    $('#continue').on('click', () => {
        socket.emit('player_next', '');
    });

    $('#vote').on('click', () => {
        var voted_player = $('#selected_player').val();

        socket.emit('player_vote', voted_player);
    });

    $('#start').on('click', () => {
        socket.emit('start_game', '');
    });

    $('#leave').on('click', () => {
        socket.emit('exit_room', '');
    });

    $('#reload').on('click', () => {
        socket.emit('reload', '');
    });

    var open_count = 0;

    $('.role_picture').on('click', () => {
        open_count = open_count + 1;
        $('.informations').addClass("show");
        $('.role_picture').addClass("show");
    });

    $('.informations').on('click', () => {
        open_count = open_count + 1;
    });

    $('body').on('click', () => {
        if(open_count == 0) {
                $('.informations').removeClass("show");
                $('.role_picture').removeClass("show");
        } else if(open_count < 0)
            open_count = 0;
        else if(open_count > 0)
            open_count = open_count - 1;
    });

    $('.input').on('focus', focusFunc);
    $('.input').on('blur', blurFunc);

    $('#mute').on('click', () => {
        socket.emit('mute_change', '');
    });

    setChoices();

    $.fn.rotate = function(degrees, step, current) {
        var self = $(this);
        current = current || 0;
        step = step || 5;
        current += step;
        self.css({
            '-webkit-transform' : 'rotate(' + current + 'deg)',
            '-moz-transform' : 'rotate(' + current + 'deg)',
            '-ms-transform' : 'rotate(' + current + 'deg)',
            'transform' : 'rotate(' + current + 'deg)'
        });
        if (current != degrees) {
            setTimeout(function() {
                self.rotate(degrees, step, current);
            }, 5);
        }
    };

    $('#reload').on('click', () => {
        var box = $('#reload')
        box.addClass("rotate");
        setTimeout(() => {
            box.removeClass("rotate");
        },2000);
    });
});


function parseInterval(value) {
    var result = new Date(1,1,1);
    result.setMilliseconds(value*1000);
    return result;
}

function secondsToHours(second) {
    var date = parseInterval(second);
    return Math.round((date.getHours())+24*(date.getDate()-1)+date.getMinutes()/60);
}

(function($) {
    $(document).ready(function(){
        var loading = $('#loading');
        $.getJSON("/api/v1/users", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(this.user_id).text(this.name));
            });
            dropdown.show();
            loading.hide();
        });
    });
})(jQuery);

var _showAvatar, _avatarFinished, _showChart, _chartFinished;

function showChart(){
    if (_chartFinished && _avatarFinished){
        $('#loading').hide();
        if(_showChart) $('#chart_div').show();
        if(_showAvatar) $('div#avatar').show();
    }
}

(function($){
    $(document).ready(function(){
        $('#user_id').change(function(){
            _showAvatar = _avatarFinished = _showChart = _chartFinished = false;
            $('div#avatar').hide();
            var avatar_img = $('img#avatar');
            avatar_img.removeAttr('src');
            avatar_img.hide();
            avatar_img.on('load', function (){
                $(this).show();
                _avatarFinished = true;
                showChart();
            });
            var real_name = $('#real_name_info');
            real_name.hide();
            var selected_user = $("#user_id").val();
            $.getJSON("/api/v1/users/"+selected_user, function(result) {
                if(result.avatar){
                    _showAvatar = true;
                    avatar_img.attr('src', result.avatar);
                    $.getJSON("/api/v1/start_end_weekday/"+selected_user,function(data){
                        _showChart = true;
                    }).error(function(){
                        _chartFinished = true;
                        $("#loading").hide();
                        real_name.empty().prepend("There is no data for the user.").show();
                    });
                }else{
                    _avatarFinished = true;
                    real_name.empty().prepend("There is no users real name.").show();
                }
                showChart();
            });
        });
    });
})(jQuery);

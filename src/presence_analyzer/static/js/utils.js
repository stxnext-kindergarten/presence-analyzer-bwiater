function parseInterval(value) {
    var result = new Date(1,1,1);
    result.setMilliseconds(value*1000);
    return result;
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

(function($){
    $(document).ready(function(){
        $('#user_id').change(function(){
            var avatar = $('#avatar');
            avatar.hide();
            var real_name = $('#real_name_info');
            real_name.hide()
            var selected_user = $("#user_id").val();
            $.getJSON("/api/v1/users/"+selected_user, function(result) {
                if(result.avatar){
                    avatar.empty().prepend("<img src='" + result.avatar + "'/>").show();
                    $.getJSON("/api/v1/start_end_weekday/"+selected_user,function(data){
                    }).error(function(){
                        $('#loading').hide();
                        real_name.empty().prepend("There is no data for the user.").show();
                    });
                }else{
                    real_name.empty().prepend("There is no users real name.").show();
                }
            });
        });
    });
})(jQuery);

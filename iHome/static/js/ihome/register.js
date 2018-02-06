function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}
var imageCodeId = ""
var preImageCodeId = ""
// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
function generateImageCode() {

    // 生成图片的uuid（图片编号）
    imageCodeId = generateUUID()

    // 生成url
    var url = "/api/v1.0/image_code?cur_id=" + imageCodeId + "&pre_id=" + preImageCodeId
    // 给图片验证码的img标签设置url
    $(".image-code>img").attr("src", url)
    // 记录当前这一次的编码，以便下一次请求的时候使用
    preImageCodeId = imageCodeId
}

function sendSMSCode() {
    // 校验参数，保证输入框有数据填写
    $(".phonecode-a").removeAttr("onclick");
    // 取到手机号
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        // 将点击事件添加回去
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    // 通过ajax方式向后端接口发送请求，让后端发送短信验证码
    var params = {
        "mobile": mobile,
        "image_code": imageCode,
        "image_code_id": imageCodeId
    }



    $.ajax({
        url: "/api/v1.0/sms_code",  // 请求地址
        type: "post",               // 请求方式
        data: JSON.stringify(params),// 请求参数
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        contentType: "application/json",// 请求参数的数据类型
        success: function (resp) {
            if (resp.errno == "0") {
                // 代表发送成功
                // 进行倒计时
                var num = 10

                var t = setInterval(function () {
                    if (num ==0) {
                        // 代表倒计时完成
                        // 清除定时器
                        clearInterval(t)
                        // 重置内容
                        $(".phonecode-a").html("获取验证码")
                        // 把点击事件添加回去
                        $(".phonecode-a").attr("onclick", "sendSMSCode();");
                    }else {
                        // 正在倒计时
                        // 去设置倒计时的秒数
                        $(".phonecode-a").html(num + "秒")
                    }
                    // 递减
                    num = num - 1
                }, 1000)

            }else {
                // 把点击事件添加回去
                $(".phonecode-a").attr("onclick", "sendSMSCode();");
                // 重新生成图片验证码
                generateImageCode()
                alert(resp.errmsg)
            }
        }
    })
}

$(document).ready(function() {
    generateImageCode();  // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });
    // 注册的提交(判断参数是否为空)

    $(".form-register").submit(function (e) {
        // 阻止默认的提交操作
        e.preventDefault()

        // 取值
        var mobile = $("#mobile").val()
        var phonecode = $("#phonecode").val()
        var password = $("#password").val()
        var password2 = $("#password2").val()

        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return
        }

        if (!phonecode) {
            $("#mphone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return
        }

        if (!password) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (password != password2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        var params = {
            "mobile": mobile,
            "phonecode": phonecode,
            "password": password
        }

        $.ajax({
            url: "/api/v1.0/users",
            type: "post",
            data: JSON.stringify(params),
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            contentType: "application/json",
            success: function (resp) {
                if (resp.errno == "0") {
                    //注册成功，进入到主页去
                    location.href = "/"
                }else {
                    $("#password2-err span").html(resp.errmsg);
                    $("#password2-err").show();
                }
            }
        })

    })
})

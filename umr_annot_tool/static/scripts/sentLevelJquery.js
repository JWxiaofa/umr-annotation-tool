$(document).ready(function(){

    //click anywhere to make the db feedback message go away
    $('body').click(function(){
        $("#error_msg").removeClass("alert alert-success alert alert-danger").empty();
    });

    // double click to set head
    $("#amr").dblclick(function(){ // when double click on element #amr
        selection = document.getSelection(); //get selection of text
        submit_template_action('set_parent'); //set text to parent
    });

    //click button to set head
    $("#set-head").click(function(){
        submit_template_action('set_parent');
    })

    // https://stackoverflow.com/questions/6658752/click-event-doesnt-work-on-dynamically-generated-elements
    $('#genericDropdown').on("click", "#sense", function() {
        $('input[name=roles]').val('');
        $('input[name=attributes]').val('');
        $('input[name=concept_types]').val('');
        $('input[name=ne_types]').val('');
        $('input[name=attribute_values1]').val('');
        $('input[name=attribute_values2]').val('');
        $('input[name=attribute_values3]').val('');
        $('input[name=attribute_values4]').val('');
        $('input[name=attribute_values5]').val('');
        $('input[name=attribute_values6]').val('');
    });
    $('#add-abs-concept').click(function() {
        $('input[name=roles]').val('');
        $('input[name=attributes]').val('');
        $('input[name=concept_types]').val('');
        $('input[name=ne_types]').val('');
        $('input[name=attribute_values1]').val('');
        $('input[name=attribute_values2]').val('');
        $('input[name=attribute_values3]').val('');
        $('input[name=attribute_values4]').val('');
        $('input[name=attribute_values5]').val('');
        $('input[name=attribute_values6]').val('');
    });
    $('#add-attr').click(function() {
        $('input[name=roles]').val('');
        $('input[name=attributes]').val('');
        $('input[name=concept_types]').val('');
        $('input[name=ne_types]').val('');
        $('input[name=attribute_values1]').val('');
        $('input[name=attribute_values2]').val('');
        $('input[name=attribute_values3]').val('');
        $('input[name=attribute_values4]').val('');
        $('input[name=attribute_values5]').val('');
        $('input[name=attribute_values6]').val('');
    });

    $('input[name=roles]').focusin(function() {
        $('input[name=roles]').val('');
    });
    $('input[name=attributes]').focusin(function() {
        $('input[name=attributes]').val('');
    });
    $('input[name=concept_types]').focusin(function() {
        $('input[name=concept_types]').val('');
    });
    $('input[name=ne_types]').focusin(function() {
        $('input[name=ne_types]').val('');
    });
    $('input[name=attribute_values1]').focusin(function() {
        $('input[name=attribute_values1]').val('');
    });
    $('input[name=attribute_values2]').focusin(function() {
        $('input[name=attribute_values2]').val('');
    });
    $('input[name=attribute_values3]').focusin(function() {
        $('input[name=attribute_values3]').val('');
    });
    $('input[name=attribute_values4]').focusin(function() {
        $('input[name=attribute_values4]').val('');
    });
    $('input[name=attribute_values5]').focusin(function() {
        $('input[name=attribute_values5]').val('');
    });
    $('input[name=attribute_values6]').focusin(function() {
        $('input[name=attribute_values6]').val('');
    });

    //used to listen for the change in replace
    document.getElementById("amr").addEventListener("input", e => {
        if(e.target.matches("span")){
            let inplaceBox = document.getElementById(e.target.id).innerHTML;
            inplaceBox = inplaceBox.replaceAll(/'/g, "\\'");
            let new_value = inplaceBox; // example: freedom-01
            // this way of dynamically changing onclick function seems ugly to me, maybe there is a better way
            let clickfunc = e.target.getAttribute("onclick"); //example: clickfunc="fillReplaceTemplate('concept','s1f','freedom','amr_elem_3')"
            let funname = clickfunc.substring(0, clickfunc.indexOf(",", clickfunc.indexOf(",") + 1)); // example: clickfunc="fillReplaceTemplate('concept','s1f'"
            document.getElementById(e.target.id).setAttribute("onclick",funname+",'"+ new_value + "','" + e.target.id + "')"); //clickfunc="fillReplaceTemplate('concept','s1f','freedom-01','amr_elem_3')"
        }
    })

    document.getElementById("amr").addEventListener("focusout", e => {
                if(e.target.matches("span")){
                    let clickfunc = e.target.getAttribute("onclick"); //example: clickfunc="fillReplaceTemplate('concept','s1f','freedom','amr_elem_3')"
                    console.log("clickfunc: ", clickfunc);

                    let type = clickfunc.replace(/fillReplaceTemplate\('(.*)','(.*)','(.*)','(.*)'\)/i, "$1");
                    let at = clickfunc.replace(/fillReplaceTemplate\('(.*)','(.*)','(.*)','(.*)'\)/i, "$2");
                    let new_value = clickfunc.replace(/fillReplaceTemplate\('(.*)','(.*)','(.*)','(.*)'\)/i, "$3");

                    let at_list = at.split(/\s+/);
                    if ((type === 'role') && (at_list) && (at_list.length >= 4) && (!at_list[2].match(/^"/))) {
                        at = at_list[0] + ' ' + at_list[1] + ' "';
                        for (let i = 2; i < at_list.length; i++) {
                            at += at_list[i] + ' ';
                        }
                        at = at.replace(/\s*$/, "\"");
                    }
                    if ((type === 'string') && new_value.match(/ /)) {
                        new_value = '"' + new_value + '"';
                    }
                    exec_command('replace ' + type + ' at ' + at + ' with ' + new_value, 1);
                }
            })

});





var savedLibraryArticles = [];
var originalRelationState = 1;
var communityEntrySortingStage = false;

function saveEntryToLibrary(){
    //Saves the current entry to the users library
    
    document.getElementById("demo").innerHTML = "The article has been saved to your library.";
}

            
function getAllClickedLibArticles() {                
/*
    Returns a list of all the library articles on the page that the user has click.
    Each library article is posted as a checkbox.            
*/
    var allLibArticles = document.getElementsByName("libArticle");
    var x = [];
    var j = 0;
    for (var i = 0; i < allLibArticles.length; ++i) {
        if (allLibArticles[i].checked) {                        
            x[j] =  allLibArticles[i].value;                    
            j += 1;
        }
    }            
    return x;
}

function getAllClickedLibArticlesAsString(){
    /*
        Also returns all the checked library articles but returns them as a space
        separated list.  This is useful for sending the article ids to the server via getJSON.                
    */

    var libList =  getAllClickedLibArticles();
    var stringOfLibArts = "";
    for(var i = 0; i < libList.length; i++){
        stringOfLibArts += libList[i];
        stringOfLibArts += " ";
    }
    return stringOfLibArts;
}




/*
    New entries are saved via a wtf form and changed from a standard html form.  The submit button has     
    been renamed and this jquery intercepts the click of the submit button and runs this funciont
    to get the library articles.
*/
$(function(){        
    $('#new_entry_submit_button').bind('click', function(e) {     
        origID = document.getElementById("original_post_id").value
        x = getSavedAndClickedAsString();
        document.getElementById("srcLibArticles").value =  x + origID; <!--libArStr; -->
        return true
    });
});





function getLibArticlesSetHiddenInput(){
    /*
        This is a helper function for the form that collects all the checked and saved library objects and then
        sets a hidden variable in the form so that all the library inputs are sent back to the server.
        
        
        !!!!!!!This has to be updated to include all the checked items and the saved items.
        
    */
    x = getSavedAndClickedAsString();
    document.getElementsByName("srcLibArticles").item(0).value =  x; <!--libArStr; -->
    return true
}

function addToSavedLib(anID, aTitle){
    /*
        There is a global array that stores all the library article inputs that 
        have been clicked.  This method takes in an id for an article and first checks
        to see if that article has been saved yet.  If the article has not been saved, 
        it stores it as a dictionary in the global variable savedLibraryArticles.
    */
    for(var i = 0; i < savedLibraryArticles.length; i++){
        if(savedLibraryArticles[i].id == anID){
            return false;
        }
    }
    savedLibraryArticles[savedLibraryArticles.length] = {"id": anID, "title": aTitle};
    return true;
}

function getSavedAndClickedAsString(){
    /*
        Collects all the saved articles
        and the clicked articles and returns it as a string.
    */
    var allClickedAndSavedLibArtIDs = getAllClickedLibArticlesAsString();
    for(var i = 0 ; i < savedLibraryArticles.length; i++){
            allClickedAndSavedLibArtIDs += savedLibraryArticles[i].id;
            allClickedAndSavedLibArtIDs += " ";
    }
    return allClickedAndSavedLibArtIDs;
}



$(function() {
    var submit_form = function(e) {
        /*
            This function is designed to do several things:
            1) save any clicked checkboxes so that they are saved on the page and the user can
            search for more library articles
            2) filter his library based on tags so that he can find articles that he feels are relevant to response
            3) clear all the library articles from the page and refresh it with new articles that have the appropriate tag
            
        */
        jQuery.ajaxSettings.traditional = true;
        var theLibFilterTags = $("#libFilterTags").val();
        var allClickedAndSavedLibArtIDs = getSavedAndClickedAsString();
        //This is the node to which we will attach the new elements
        var savedLibNode = $("#savedLibArticles"); 
        $.getJSON($SCRIPT_ROOT + '/_filter_lib_articles', {
            tags: theLibFilterTags,
            savedLibArticleIds : allClickedAndSavedLibArtIDs
        }, function(data) {            
            if(!$("#savedLibElem").length && data.entriesForSavedList.length){
                    var txtNode = document.createTextNode("Your input articles so far :")
                    txtNode.id = "inputLibraryTitle";
                    savedLibNode[0].appendChild(txtNode);
                    savedLibNode[0].appendChild(document.createElement("br"));
            }
            for(var i = 0; i < data.entriesForSavedList.length ; i++) {                
                if(addToSavedLib(data.entriesForSavedList[i].id, data.entriesForSavedList[i].title)){
                    var savedLibEl = document.createElement("a");
                    savedLibEl.id = "savedLibElem";
                    savedLibEl.value = data.entriesForSavedList[i].id;
                    savedLibEl.innerHTML = data.entriesForSavedList[i].title;
                    savedLibEl.href = $SCRIPT_ROOT + '/write_response/' + data.entriesForSavedList[i].id.toString();
                    savedLibNode[0].appendChild(savedLibEl);                        
                    savedLibNode[0].appendChild(document.createElement("br"));
                }
                
            }
            var node = $('#libArticlesList');
            node.empty();     
            for(var i = 0 ; i < data.libArticles.length; i++){

                // alert(JSON.stringify(data.libArticles[i]));

                tags = '';
                tagArray = data.libArticles[i].tags.split(" ");
                for(var j = 0; j < tagArray.length; j++){
                    tags += '<span class="label label-default margin-right-five">' + tagArray[j] + '</span>';
                }


                entryHTML = '<div class="panel panel-default"><div class="panel-body"><div class="media media-clearfix-xs-min">' +
                    '<div class="media-body"><input type="checkbox" class="selectLibArticle" name="libArticle" value=' + data.libArticles[i].id +  '>' +
                    '<h3 class="media-heading h4"><a href=/write_response/' + data.libArticles[i].id + '>'+ data.libArticles[i].title +'</a></h3>' +
                    '<p class="small text-muted"><i class="fa fa-user fa-fw"></i> <a href=/public_user_page/'+ data.libArticles[i].user_id + '>' + data.libArticles[i].user_name +'</a> ' +
                    '<i class="fa fa-calendar fa-fw"></i>' + data.libArticles[i].timestamp + ' </p>' + tags;

                $("#libArticlesList").append(entryHTML);




                    // <span class="label label-default">Entry</span> <span class="label label-default">Tag</span> </div> </div> </div> </div>';

                //Create checkbox dynamically       
//                 var cb = document.createElement( "input" );
//                 cb.type = "checkbox";
//                 cb.name = "libArticle";
//                 cb.value = data.libArticles[i].id;
//                 cb.label = data.libArticles[i].title;
//                 cb.checked = false;
//                 var br = document.createElement("br");
//                 node[0].appendChild(br);
//                 node[0].appendChild(cb);
//                 var a = document.createElement('a');
// //                var linkText = document.createTextNode((data.libArticles[i].title).bold());
//                 var linkText = document.createElement("b");
//                 linkText.innerHTML = data.libArticles[i].title
//                 a.appendChild(linkText);
//                 a.title = data.libArticles[i].title;
//                 a.href =  $SCRIPT_ROOT + '/write_response/' + data.libArticles[i].id.toString();
//                 var br = document.createElement("br");
//                 node[0].appendChild(a);
//                 var br = document.createElement("br");
//                 node[0].appendChild(br);
//                 var theTxt = document.createTextNode(data.libArticles[i].text);
//                 node[0].appendChild(theTxt);
//                 var br = document.createElement("br");
//                 node[0].appendChild(br);
//                 node[0].appendChild(document.createTextNode("Tags: " + data.libArticles[i].tags))
//                 var br = document.createElement("br");
//                 node[0].appendChild(br);
            }                    
        });              
        return false;
    };
    $('#libTagFilterButton').bind('click', submit_form);
    $('input[id = "libFilterTags"]').bind('keydown', function(e) {
      if (e.keyCode == 13) {
        submit_form(e);
      }
    });
  });
  
/*
    When deciding on a relationship between entries, a user 
    can swap the direction of the relationship. This function
    does that by going to the server and getting all the relationship types
    and swaps their meaning.  It also sets a global variable that defines 
    the relationship direction.
*/
$(function(){        
    $('#relReverseButton').bind('click', function(e) {
        var relTypeListNode = $('#relTypeList')
        relTypeListNode.empty();
        jQuery.ajaxSettings.traditional = true;
        //This is the node to which we will attach the new elements
        var buttonListNode = $("#relTypeList"); 
        $.getJSON($SCRIPT_ROOT + '/_reverse_relation_types', function(data) {
            for(var i = 0; i < data.relationTypes.length; i++){
                var name = data.relationTypes[i].name;
                var relID = data.relationTypes[i].id;
                var desc = data.relationTypes[i].descriptor;
                var cb = document.createElement( "input" );
                cb.type = "radio";
                cb.name = "arComp"
                cb.value = data.relationTypes[i].id;
                cb.id = data.relationTypes[i].id;
                if (name == "no relation") {
                    cb.checked = true;
                }
                else {
                    cb.checked = false;                
                }
                if(originalRelationState > 0){
                    var theTxt = document.createTextNode("Article B " + desc + " article A.");
                    document.getElementsByName("isReversed").item(0).value =  1
                }else {
                    var theTxt = document.createTextNode("Article A " + desc + " article B.");
                    document.getElementsByName("isReversed").item(0).value =  0
                }                
                var p = document.createElement("dd");
//                p.class = "tab";
                buttonListNode[0].appendChild(p);
                buttonListNode[0].appendChild(cb);
                buttonListNode[0].appendChild(theTxt);
                var br = document.createElement("br");                
                buttonListNode[0].appendChild(br);            
            }
            originalRelationState *= -1;
        });
    });
});

/*
    This is a simple function used save an entry to a user's library.
    If the article is added to the library, a message is printed to that effect.
*/
$(function(){        
    $('#saveToLibButton').bind('click', function(e) {        
        $.getJSON($SCRIPT_ROOT + '/_save_to_read_history',{
            original_id : $("#original_post_id").val()
        }, function(data) {    
            buttonDiv = document.getElementById("saveToLibButton");
            buttonDiv.remove();
            document.getElementById("SaveToLibResponse").innerHTML = String(data.returnString);
        });        
    });
});



/*
    This function checks to see if a user has any updates.  The function is run
    everytime the user relaods/loads any page on the site.  It goes to the server
    and checks for updates.  If there are updates, then a new link is added to the top
    banner indicating the number of new updates.

$( document ).ready(function() {    
    $.getJSON($SCRIPT_ROOT + '/_get_user_update', function(data) {
        if( data.updates.length > 0 ) {
            var bannerNode = $("#banner");             
            var a = document.createElement('a');
            var linkText = document.createElement("b");
            linkText.innerHTML = "| You have " + String(data.updates.length) + " new updates |";
            a.appendChild(linkText);
            a.href =  $SCRIPT_ROOT + '/show_updates/';
            bannerNode[0].appendChild(a)
        }
        
    });
});
    
*/

$(document).ready ( function () {
    /*
        Users can get updates about new responses and communities.  These are 
        listed on an update page.  When a user clicks on a link, it runs this function.
    */
    $(document).on ("mousedown", "#updateLink", function (e) {
       if( e.which === 3 ) {
            e.preventDefault();      
        }
        var updateID = e.target.attr("value")
        $.getJSON($SCRIPT_ROOT + '/clear_update', {
            updateID : updateID
        }, function(data) {
            
        });
    });
});



/*
    When the user clicks the sort by supports button on the communities page,
    this function is called which goes to the server and gets 
    a list of all the entries in the community sorted by the given 
    parameter.
*/
$(function(){        
    $('#sort_by_button, #sort_by_date').bind('click', function(e) {        
        var sort_switch_val = $(this).val()
        $.getJSON($SCRIPT_ROOT + '/sort_community_entries_by',{
            comm_id : $("#comm_sort_by_hidden").val(),
            is_reversed : communityEntrySortingStage,
            sort_switch : $(this).val()
        }, function(data) {    
            var commEntriesListNode = $("#comm_entries_list");   
            commEntriesListNode.empty();
            for(var i = 0 ; i < data.comm_entries.length; i++){                
                var a = document.createElement('a');
                var linkText = document.createElement("b");
                linkText.innerHTML = data.comm_entries[i].title;
                a.appendChild(linkText);
                a.title = data.comm_entries[i].title;
                a.href =  $SCRIPT_ROOT + '/full_display_entry/' + data.comm_entries[i].id.toString();
                var br = document.createElement("br");
                commEntriesListNode[0].appendChild(a);
                var br = document.createElement("br");
                commEntriesListNode[0].appendChild(br);
                if(sort_switch_val == 0){
                    if(!communityEntrySortingStage){
                        var theTxt = document.createTextNode("Number of Supporting Entries : " + data.comm_entries[i].num_descendants );
                    }
                    else{
                        var theTxt = document.createTextNode("Number of Entries this Supports : " + data.comm_entries[i].num_descendants );
                    }
                    commEntriesListNode[0].appendChild(theTxt);
                    var br = document.createElement("br");
                }                
                commEntriesListNode[0].appendChild(br);
                var theTxt = document.createTextNode("Tags : " + data.comm_entries[i].tags);
                commEntriesListNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                commEntriesListNode[0].appendChild(br);
                var theTxt = document.createTextNode("Date posted : " + data.comm_entries[i].date_posted);
                commEntriesListNode[0].appendChild(theTxt);
                var p = document.createElement("p");
                commEntriesListNode[0].appendChild(p);               
            }
            communityEntrySortingStage = !communityEntrySortingStage;
        });
    });
});


/*
    This is a jquery function that goes to the database and gets a list of users
    and then prints them.
*/
function get_user_from_database(){
        var user_name_search_string = $("#user_name_search_string").val();
        var actionString = $("#admin_action_type").val();
        $.getJSON($SCRIPT_ROOT + '/get_user_for_admin_purposes',{
            user_name_search_string : user_name_search_string
        }, function(data) {
            var userNode = $("#list_of_users");
            userNode.empty();
            for(var i = 0; i < data.users.length; i++){
                var cb = document.createElement( "input" );
                cb.type = "radio";
                cb.value = data.users[i].user_ID;
                cb.checked = false;    
                cb.name = "selected_user";                
                userNode[0].appendChild(cb);
                var theTxt = document.createTextNode(data.users[i].user_name);
                userNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                userNode[0].appendChild(br);
                var theTxt = document.createTextNode("Date joined : " + data.users[i].date_joined);
                userNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                userNode[0].appendChild(br);
                var theTxt = document.createTextNode("User Role : " + data.users[i].role);
                userNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                userNode[0].appendChild(br);
                var theTxt = document.createTextNode("User Email : " + data.users[i].email);  
                userNode[0].appendChild(theTxt);
                var p = document.createElement("p");
                userNode[0].appendChild(p);
            }
            var userNode = $("#list_of_users");
            var aButton = document.createElement("input");
            aButton.type = "submit";
            aButton.value = actionString;
            userNode[0].appendChild(aButton);
        });   
}

function print_list_of_users_create_button(data, actionString){
            var userNode = $("#list_of_users");
            userNode.empty();
            for(var i = 0; i < data.users.length; i++){
                var cb = document.createElement( "input" );
                cb.type = "radio";
                cb.value = data.users[i].user_ID;
                cb.checked = false;    
                cb.name = "selected_user";                
                userNode[0].appendChild(cb);
                var theTxt = document.createTextNode(data.users[i].user_name);
                userNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                userNode[0].appendChild(br);
                var theTxt = document.createTextNode("Date joined : " + data.users[i].date_joined);
                userNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                userNode[0].appendChild(br);
                var theTxt = document.createTextNode("User Role : " + data.users[i].role);
                userNode[0].appendChild(theTxt);
                var br = document.createElement("br");
                userNode[0].appendChild(br);
                var theTxt = document.createTextNode("User Email : " + data.users[i].email);  
                userNode[0].appendChild(theTxt);
                var p = document.createElement("p");
                userNode[0].appendChild(p);
            }
            var userNode = $("#list_of_users");
            var aButton = document.createElement("input");
            aButton.type = "submit";
            aButton.value = actionString;
            userNode[0].appendChild(aButton);
    
}

/*
    This is a jquery function that goes to the database and gets a list of users
    and then prints them.
*/
function get_user_common_community_from_database(){
        var user_name_search_string = $("#user_name_search_string").val();
        var actionString = $("#admin_action_type").val();
        $.getJSON($SCRIPT_ROOT + '/get_user_with_common_communities',{
            user_name_search_string : user_name_search_string
        }, function(data) {
            var userNode = $("#list_of_users");
            print_list_of_users_create_button(data, actionString);
            if(data.users.length == 0){
                var theTxt = document.createTextNode("No one in your communities matches that user name.");  
                userNode[0].appendChild(theTxt);
                var p = document.createElement("p");
                userNode[0].appendChild(p);
            }
        });   
}


/*
    Administrators are able to assign moderator status to users.
    This function is a search function that allows moderators to
    enter a user name or part of it and it returns a list of users
    and prints them tot he "add mod status" page.
*/
$(function(){        
    $('#user_name_search_button_assign_moderator').on('click', function(e) {  
        get_user_from_database();
        });
});


/*
    Administrators are able to ban users.
    This function is a search function that allows moderators to
    enter a user name or part of it and it returns a list of users
    and prints them tot he "add mod status" page.
*/
$(function(){        
    $('#user_name_search_button_delete_user').on('click', function(e) {  
        get_user_from_database();
    });
});


/*
    Users need to search for other users to send them a private
    message.
*/
$(function(){        
    $('#user_name_search_button').on('click', function(e) {  
        get_user_common_community_from_database();
        });
});
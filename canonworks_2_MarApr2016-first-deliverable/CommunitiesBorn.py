'''
This is the main application for Communities Born.  This will be a Flask website.
Created on Oct 20, 2014

@author: Ben Sprott
'''
# all the imports
import os
import platform
import signal
import sys
import random
import traceback
import string
import re
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, make_response, jsonify, send_from_directory
from contextlib import closing
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from EntryMatching.CompareEntries import CompareEntries
from flask_bootstrap import Bootstrap
from flask_script import Manager
from models import *
from auth.forms import LoginForm, RegistrationForm, ForgotPassword, ResetPassword, ChangeEmail, NewEntry, NewPrivateMessage, PrivateMessageReply
from datetime import date, datetime
from LimitedStream import StreamConsumingMiddleware
from werkzeug import secure_filename
from Queue import PriorityQueue
from decorators import admin_required, mod_required, write_required
from sqlalchemy import and_
from flask_mail import Mail, Message
from threading import Thread
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_pagedown import PageDown
from HTMLParser import HTMLParser

from tzlocal import get_localzone

testAndDebug = True
paginationDebug = False


#create a pagedown instance
pagedown = PageDown()        

# create our little application :)
app = Flask(__name__)

pagedown.init_app(app)
# configuration
if "linux" in (sys.platform).lower() :
    #DATABASE = 'sqlite:////home/canonworks/canonApp/thecanonworks/firstDB.db'
    DATABASE =  '/home/shile/thecanonworks/CanonworksMayRelease/firstDB.db'
    UPLOAD_FOLDER = '/home/thecanonworks/CanonworksMayRelease/static/images/'
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    
    
elif "win" in (sys.platform).lower() :
    app.wsgi_app = StreamConsumingMiddleware(app.wsgi_app)
    DATABASE = 'C:\\flaskDB\\commBorn14.db'
    UPLOAD_FOLDER = 'C:\\Users\\BenGaming\\git\\canonworksFeb2016\\static\\images\\'
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587

elif "darwin" in (sys.platform).lower() :
    pass
    
else :
    pass


app.config['CANONWORKS_MAIL_SUBJECT_PREFIX'] = '[The Canonworks]'
app.config['CANONWORKS_MAIL_SENDER'] = ['The Canonworks Admin <admin@thecanonworks.com>']  
app.config['MAIL_USE_TLS'] = True    
app.config['MAIL_USERNAME'] = os.environ.get('CAN_MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('CAN_MAIL_PASSWORD')
app.config['CANON_POSTS_PER_PAGE'] = 10
mail = Mail(app)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER    
    
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
current_user_name = None
successful_relationship_type_vote_threshold = 0


from auth import auth as auth_blueprint
app.config.from_object(__name__)
app.register_blueprint(auth_blueprint, url_prefix = '/auth')
entComp = CompareEntries(g)
app.config['CANONWORKS_ADMIN'] = "shilefasugba@gmail.com"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE
app.config['SECURITY_REGISTERABLE'] = True
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SECRET_KEY'] = 'K*JH67Hj%G$J*jhHJU*RTGdre2@G0LKBCXDSfG@$h'
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
Bootstrap(app)
manager = Manager(app)
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])




alchemyDB.init_app(app)
with app.app_context():
        # Extensions like Flask-SQLAlchemy now know what the "current" app
        # is while within this block. Therefore, you can now run........
    alchemyDB.create_all()

Roles.setRolesInDB(app)
ResponseRelationTypes.setRelationTypesInDB(app)
UserRelationshipType.setUserRelationshipsInDatabase(app)



'''
    Test and debug scripting
'''

with app.app_context():
    if paginationDebug :
        anEntry = Entries.query.all()        
        if len(anEntry) != 0 :
            print("last entry id : " + str(anEntry[-1].id))
        if len(anEntry) == 0 or anEntry[-1].id < 98:
            Entries.generate_fake()








@app.route('/create_entry', methods=['GET', 'POST'])
@write_required
@login_required
def create_entry() :
    
    
    if not current_user.email_confirmed and not testAndDebug:
        flash("You need to confirm your email to post a new entry!")
        return redirect(url_for('index'))
    entryObjList = [a.library_entry for a in current_user.user_library.all()]  
    entryObjList.extend(current_user.users_entries)
    userLibEntries = convertEntryListToDictList(entryObjList)     
    form = NewEntry()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit() :    
        tags = form.tags.data
        tagList = splitA_TagStringByCommaAndSpace(tags)
        tagObjectList = addNewTagsFromList(tagList)
        anEntry = Entries(title = form.title.data,text = form.text.data, user_id = current_user.id)          
        alchemyDB.session.add(anEntry)
        alchemyDB.session.flush()        
        anEntry.tags.extend(tagObjectList)        
        create_src_to_output_rel(form.srcLibEntries.data, anEntry.id)      
        alchemyDB.session.commit()
        flash('New entry was successfully posted!')        
        return redirect(url_for('index'))
    return render_template('create_new_entry.html', userLib = userLibEntries, form = form)    


@app.route('/')
def index(entries = None):
    if entries == None :
        page = request.args.get('page', 1, type=int)
        pagination = Entries.query.order_by(Entries.date_posted.desc()).paginate(page, per_page=current_app.config['CANON_POSTS_PER_PAGE'], error_out = False)
        entries = pagination.items
    else :
        page = request.args.get('page', 1, type=int)
        pagination = entries.paginate(page, per_page=current_app.config['CANON_POSTS_PER_PAGE'], error_out = False)
    background = None
    avatar = None
  
    
    return render_template('index.html', entries=convertEntryListToDictList(entries), background = background, avatar = avatar, pagination = pagination)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You were logged out')
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # @UndefinedVariable



@app.route("/edit_entry/<int:id>", methods=["GET", "POST"])
def edit_entry(id):
    '''
         a route to allow for the editing of a
         an entry.         
    '''
    entry = Entries.query.get_or_404(id)
    if current_user != entry.user_who_created and not current_user.can(Permission.ADMINISTER) :
        abort(403)
    form = NewEntry()
    if form.validate_on_submit() :
        entry.text = form.text.data
        tags = form.tags.data
        tagList = splitA_TagStringByCommaAndSpace(tags)
        tagObjectList = addNewTagsFromList(tagList)
        entry.tags = tagObjectList
        alchemyDB.session.add(entry)
        alchemyDB.session.commit()
        flash("The post has been updated.")
        return redirect(url_for("view_latest_posts"))
    form.title.data = entry.title
    form.text.data = entry.text
    form.tags.data = " ".join([x.tag for x in entry.tags])
    entryObjList = [a.library_entry for a in current_user.user_library.all()]  
    entryObjList.extend(current_user.users_entries)
    userLibEntries = convertEntryListToDictList(entryObjList)
    return render_template("edit_entry.html", form = form, userlib = userLibEntries)

        
    


@app.route('/add', methods=['POST'])
@write_required
@login_required
def add_entry():  

    form = NewEntry()    
    if form.validate_on_submit() :
        tags = form.tag.data
        tagList = splitA_TagStringByCommaAndSpace(tags)
        tagObjectList = addNewTagsFromList(tagList)
        anEntry = Entries(title = form.title.data,text = form.text.data, user_id = current_user.id)     
        alchemyDB.session.add(anEntry)
        alchemyDB.session.flush()
        anEntry.tags.extend(tagObjectList)
        create_src_to_output_rel(request.form['srcLibArticles'], anEntry.id)
        alchemyDB.session.commit()
        flash('New entry was successfully posted!')
        return redirect(url_for('show_entries'))
    return render_template("")
        
    

def verify_password(username, password):
    '''
     verifies passwords
    '''
    passQuery = g.db.execute('select user_name, user_pass from users where user_name="%s"' %username)
    passHash = passQuery.fetchone()
    if not passHash :
        return False
    passHash = passHash[1]
    return check_password_hash(passHash, password)

def getAllUsersTags(user):
    '''
        get all tags that a user has applied to their articles
    '''
    tags = set()
    all_users_tags = [x.tags for x in current_user.users_entries]
    for tagList in all_users_tags :
        for tag in tagList :
            tags.add(tag.tag)
    return list(tags)
    
def convertUserToJinjaDict(user):
    '''
        converts a user to a user dictionary
    '''
    return {'id': user.id,\
            'name':user.user_name,\
            'email':user.user_email,'role':user.role.name,\
            'date_joined':user.date_joined,\
            'communities':convertCommunityListToJinjaDictList([x.community for x in user.users_communities.all()]),\
            'entries': convertEntryListToDictList(user.users_entries),\
            'tags':getAllUsersTags(user),\
            'bio':user.user_biography,\
            'date_of_birth':user.date_of_birth, \
            'banned': user.role.name == "Banned",\
            'library' : convertEntryListToDictList([x.entry for x in user.user_library.all()])}
    
@app.route('/private_user_profile', methods=['GET', 'POST'])
@login_required
def private_user_profile():
    '''
        show user profile

        
    '''
    return render_template('user-private-profile.html', user = convertUserToJinjaDict(current_user))



@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
        Allows the user to register
    '''

    if not current_user.is_authenticated :
        form = RegistrationForm()
        if form.validate_on_submit():            
            user = User(user_email = form.email.data, user_name = form.username.data, password = form.password.data,  role_id = Roles.query.filter_by(name = 'User').first().id, date_joined = datetime.now())
            alchemyDB.session.add(user)  # @UndefinedVariable
            alchemyDB.session.commit()  # @UndefinedVariable
            token = user.generate_confirmation_token()
            send_email(user.user_email, "Confirm Your Account", 'auth/email/confirm', user=user,token=token)
            flash('A confirmation email has been sent to you by email.')
            if app.config['CANONWORKS_ADMIN'] :
                send_email(app.config['CANONWORKS_ADMIN'], 'New User', 'mail/new_user', user = user)                
            flash('You can now login.')
            return redirect(url_for('auth.login'))
        return render_template('auth/register.html', form = form)
    return redirect(url_for('index'))


@app.route('/confirm/<token>')
@login_required
def confirm(token):
    '''
        This confirms a user's email address
    '''
    if current_user.email_confirmed :
        flash("Your email was already confirmed!")
        return redirect(url_for("view_latest_posts"))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else :
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('view_latest_posts'))

@app.route('/view_articles_with_matches')
@login_required
def view_articles_having_matches():
    '''
        allows the user to view his matches
    '''
    users_relations = []
    confRels = ConfirmedSrcOutRelType.query.all()
    for confRel in confRels :
        srcOut = confRel.src_out_rel
        source = srcOut.source
        output = srcOut.output
        if source.user_who_created == current_user :
            users_relations.append(source)
        elif output.user_who_created == current_user :
            users_relations.append(output)
            
    return render_template('view_articles_with_matches.html', articles = users_relations)

def convertSrcTargetPairListToDictList(srcTargPairList):
    '''
        to get a nice print out of  some source target pairs, we need
        to convert a list of source target pairs into a nice list of dictionaries
        that can be sent back to the page for rendering.
    '''
    outDictList = []
    for pair in srcTargPairList :
        source = pair[0]
        target = pair[1]
        outDict = createSrcEntryPairDict(source, target, pair[2])
        outDictList.append(outDict)
    return outDictList

def convertSrcTargListToEntryList(srcTargetList):
    '''
        to compare entries and to filter comparable entries via tags,
        we start with callling the list of src to target objects 
        and then convert this to a list of entries.  The user can then
        filter src to target entries on keywords.
    '''
    outputEntries = []
    for srcTar in srcTargetList :
        outputEntries.append([srcTar.source, srcTar.output, srcTar.id])
    return outputEntries

@app.route('/filter_articles_to_compare', methods = ['GET', 'POST'])
@login_required
def filter_articles_to_compare():
    '''
        Users who are willing to compare articles will want to filter on tags
        so that they can compare articles that are relevant to them.
    '''
    desiredTags = splitA_TagStringByCommaAndSpace(request.form['tags'])
    if len(desiredTags) == 0 :
        return redirect('compare_articles')        
    relations = SourceToOutputRelation.query.filter(SourceToOutputRelation.needs_processing == True).all()
    modifiedRelList = []    
    for rel in relations :
        for entryTag in rel.output.tags.all() :
            if entryTag.tag in desiredTags :
                modifiedRelList.append(rel)
                break
    modifiedRelList = filterSrcOuputRelListForUser(modifiedRelList)
    return render_template('choose_entries_to_compare.html', relations = convertSrcTargetPairListToDictList(convertSrcTargListToEntryList(modifiedRelList)))

def filterSrcOuputRelListForUser(srcOutList):
    '''
        we want to ensure that users never compare their own articles.
        This function takes in a list of source output relation objects
        and filters out any that may have the user as either source or output.
    '''
    newList = []
    for srcOutRel in srcOutList :
        if (srcOutRel.source.user_id != current_user.id) and (srcOutRel.output.user_id != current_user.id) :
            newList.append(srcOutRel)
    return newList

def filterSrcOutputRelListForVotesByUser(srcOutList):
    '''
        If the user has already voted for this relationship, remove it from the list.
    '''
    newList = []    
    for srcTar in srcOutList :
        alreadyVoted = False
        for vote in srcTar.votes_for_this_rel.all() :
            if vote.user == current_user :
                alreadyVoted = True
                break
        if not alreadyVoted:
            newList.append(srcTar)
    return newList


@app.route('/compare_articles', methods = ['GET', 'POST'])
@login_required
def compare_articles():
    '''
        Allows users to compare articles

            tests:
                1. test with empty entries database
                2. test with only one entry

    '''
    articles_to_compare = SourceToOutputRelation.query.filter(SourceToOutputRelation.needs_processing == True).all()[:100]       
    articles = convertSrcTargetPairListToDictList(convertSrcTargListToEntryList(filterSrcOutputRelListForVotesByUser(filterSrcOuputRelListForUser(articles_to_compare))))
    if articles == [] :
        flash("No articles need comparing.")
        return redirect(url_for('view_latest_posts'))
    
    return render_template('choose_entries_to_compare.html', relations=articles)



def createSrcEntryPairDict(source, target, id):
    '''
        takes a pair of entries, understood as the source and target of a relation
        and returns a dictionary breakout of the fields
    '''
    srcDict = convertEntryObjectTDict(source)
    tarDict = convertEntryObjectTDict(target)
    outDict = {'id' : id, 'srcDict' : srcDict, 'tarDict':tarDict}
    return outDict

@app.route('/compare_these_articles/<srcTrgtID>', methods = ['GET', 'POST'])
@login_required
def compare_these_articles(srcTrgtID):
    '''
        once we have gotten two articles to compare, we
        can compare them
        
        input : id is the id of the         
    '''
    
    srcTargetObj = SourceToOutputRelation.query.filter(SourceToOutputRelation.id == srcTrgtID).first()
    srcDict = convertEntryObjectTDict(srcTargetObj.source)
    tarDict = convertEntryObjectTDict(srcTargetObj.output)
    relTypes = [{"desc" : x.descriptor, "id" : x.id, "name":x.name} for x in ResponseRelationTypes.query.all()]
    print(srcDict['body_html'])
    if current_user.id != srcDict["userID"] and current_user.id != tarDict["userID"] :
        return render_template('compare_these_articles.html', srcTrgID = srcTrgtID, srcDict=srcDict, targDict=tarDict, relTypes = relTypes)
    else :
        flash("You do not have permission to vote on these articles!")
        return redirect(url_for(index))


@app.route('/_reverse_relation_types', methods = ['GET', 'POST'])
@login_required
def reverse_relation_types():
    '''
        this is meant to be called by jquery so that if 
        a user needs to reverse the relation types
        they can get all the types back.
    '''
    relTypes = [{'name' : x.name, 'id' : x.id, 'descriptor':x.descriptor} for x in ResponseRelationTypes.query.all()]
    return jsonify(relationTypes = relTypes)


def convertTagListToTagNameList(tagList):
    '''
        takes a list of tag objects and returns a list of
        tag names (strings)
    '''
    return [x.tag for x in tagList]
    


def convertSrcOutListToJinjaDictList2(respList):
    '''
        We want to build a page of responses based on source Output relations.
        Here we convert a list of source out relations into a list of dictionaries
        which can be parsed by Jinja.
    '''
    dictList = []    
    for srcOut in respList :
        orig_title = srcOut.source.title
        out_title = srcOut.output.title
        response_user = srcOut.output.user_who_created.user_name
        origin_user = srcOut.source.user_who_created.user_name             
        dictList.append({'src_title' : orig_title,
                         'out_title'  : out_title,
                         'tags' : " ".join(list(set(convertTagListToTagNameList(srcOut.source.tags) + convertTagListToTagNameList(srcOut.output.tags)))),
                         'date' : srcOut.confirmedRelType.date_of_confirmation,
                         'response_type' : srcOut.confirmedRelType.resp_rel_type.name,
                         'response_user' : response_user,
                         'origin_user' : origin_user,
                         'srcOutID' : srcOut.id})
    return dictList


@app.route('/latest_responses/', methods = ['GET', 'POST'])
@login_required
def latest_responses() :
    '''
        we are going to list all the responses.
    '''
    
    responses = []
    for resp in SourceToOutputRelation.query.filter_by(needs_processing = False).all() :
        if resp.confirmedRelType.resp_rel_type.name != "no relation" :
            responses.append(resp)
    responses.sort(key=lambda x: x.date_related, reverse=True)
    return render_template("latest_responses.html", responses = convertSrcOutListToJinjaDictList2(responses))

@app.route('/latest_communities/', methods = ['GET', 'POST'])
def latest_communities() :
    '''
        we are going to list all the communities according to
        an algorithm that sorts them.
    '''
    communities = Communities.query.all()
    communities.sort(key=lambda x: len(x.users_in_this_community.all()), reverse=True)
    commDictList =  convertCommunityListToJinjaDictList(communities)
    return render_template("latest_communities.html", commList = commDictList)



def getAllUsersConfirmedResponses(aUser):
    '''
        Given a user, find all their responses that 
        have been confirmed but not confirmed as no relationship.
    '''
    confEntries = []
    srcOutRels = SourceToOutputRelation.query.filter_by(needs_processing = False)
    for srcOut in srcOutRels :
        if srcOut.source.user_who_created == aUser or srcOut.output.user_who_created == aUser :
            if srcOut.confirmedRelType.resp_rel_type.descriptor != "no relation" :
                confEntries.append(srcOut)
    return confEntries

def convertSrcOutListToJinjaDictList(respList):
    '''
        We want to build a page of responses based on source Output relations.
        Here we convert a list of source out relations into a list of dictionaries
        which can be parsed by Jinja.
    '''
    dictList = []    
    for srcOut in respList :
        if current_user != srcOut.source.user_who_created :
            responder = srcOut.source.user_who_created.user_name
            out_title = srcOut.source.title
            orig_title = srcOut.output.title
        elif current_user != srcOut.output.user_who_created :
            responder = srcOut.output.user_who_created.user_name            
            out_title = srcOut.output.title
            orig_title = srcOut.source.title
        else :
            responder = "You"
            out_title = srcOut.output.title
            orig_title = srcOut.source.title
        dictList.append({'src_title' : orig_title,
                         'out_title'  : out_title,
                         'tags' : convertTagQueryIntoTagString(srcOut.source.tags) + " " + convertTagQueryIntoTagString(srcOut.output.tags),
                         'date' : srcOut.confirmedRelType.date_of_confirmation,
                         'response_type' : srcOut.confirmedRelType.resp_rel_type.name,
                         'responder' : responder,
                         'srcOutID' : srcOut.id})
    return dictList

@app.route('/your_responses/', methods = ['GET', 'POST'])
@login_required
def your_responses():
    '''
        This is a page to view all the responses to your posts that have been
        successfully confirmed.
    '''
    responses = getAllUsersConfirmedResponses(current_user)
    return render_template('your_responses.html', responses = convertSrcOutListToJinjaDictList(responses))

def buildResponsePageDict(srcOutRelation):
    '''
        Here we build the response page dictionary.
    '''    
    thePageDict = {}
    thePageDict['source_art'] =  convertEntryObjectTDict(srcOutRelation.source)
    thePageDict['target_art'] =  convertEntryObjectTDict(srcOutRelation.output)
    thePageDict['relationType'] =  srcOutRelation.confirmedRelType.resp_rel_type.descriptor
    thePageDict['isReversed'] =  srcOutRelation.confirmedRelType.is_reversed
    thePageDict['dateConfirmed'] =  str(srcOutRelation.confirmedRelType.date_of_confirmation)[:10]
    thePageDict['users'] =  [srcOutRelation.source.user_who_created.user_name, srcOutRelation.output.user_who_created.user_name]
    thePageDict['tags'] = " ".join(set([tag.tag for tag in srcOutRelation.source.tags] + [tag.tag for tag in srcOutRelation.output.tags]))
    return thePageDict


@app.route('/response_page/<src_out>', methods = ['GET', 'POST'])
def response_page(src_out):
    '''
        We use this route to display a response.
    '''
    srcOutRel = SourceToOutputRelation.query.filter_by(id = src_out).first()    
    return render_template('response_page.html', respPageData = buildResponsePageDict(srcOutRel))

@app.route('/full_display_entry/<id>', methods=['GET', 'POST'])
def full_display_entry(id):
    '''
        When browsing the entries in a community, we might want to
        click on an entry and see all it's sources and outputs.  This
        does that.
    '''
    entry = ""
    sources = ""
    outputs = ""
    return render_template('full_display_entry.html', entry = entry, sources = sources, outputs = outputs)


def getAllCommunityEntriesSortedByDate(community, reversed):
    '''
        We may want all community entries sorted by date.
    '''
    
    allEntries = {}
    for commEntEnt in community.srcOutRelations_in_this_community.all() :
        srcOut = commEntEnt.srcOutRelation
        if allEntries.get(srcOut.source) == None :
            allEntries[srcOut.source] = 0
        if allEntries.get(srcOut.output) == None :
            allEntries[srcOut.output] = 0
    entries = allEntries.keys() 
    entries.sort(key=lambda x: x.date_posted, reverse=reversed)
    return convertEntryListToDictList(entries)

@app.route('/sort_community_entries_by', methods = ['GET', 'POST'])
def sort_community_entries_by():
    '''
        allows a user to filter library articles on tags when creating a response article
    '''
    commID = request.args.get("comm_id", "", type=str)
    isReversed = request.args.get("is_reversed") == 'true'
    community = Communities.query.filter_by(id = commID).first()
    sortType = request.args.get("sort_switch")
    
    if sortType == '0' :    
        if isReversed :
            entries = entryDescendantPairListToDictList(getListOfEntriesSortedByAmountThisEntrySupports(community))
        else :
            entries = entryDescendantPairListToDictList(getListOfEntriesSortedByAmountOfSupport(community))
    elif sortType == '2' :
        entries = getAllCommunityEntriesSortedByDate(community, isReversed)                    
    else :
        entries = []        
    return jsonify(comm_entries = entries)

@app.route('/set_community_description/<commID>', methods = ['GET', 'POST'])
@login_required
def set_community_description(commID):
    '''
        allows community members to set the community text
    '''    
    
    aComm = Communities.query.filter_by(id = commID).first()
    if current_user.is_in_this_community(aComm) :
        aComm.page.eplanation_text = request.form['comm_desc']
        alchemyDB.session.commit()
        flash("Set the community description!")
    else :
        flash("You are not in that community!")
    return redirect(url_for('display_community', commID = commID))
    

@app.route('/set_community_name/<commID>', methods = ['GET', 'POST'])
@login_required
def set_community_name(commID):
    '''
        set the community name
    '''
    aComm = Communities.query.filter_by(id = commID).first()
    if current_user.is_in_this_community(aComm) :
        aComm.community_name = request.form['comm_name']
        aComm.page.community_name = request.form['comm_name']
        alchemyDB.session.commit()
        flash("Changed the community name!")
    else :
        flash("You are not in that community!")
    return redirect(url_for('display_community', commID = commID))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload_community_image/<commID>/', methods = ['GET', 'POST'])
@login_required
def upload_community_image(commID):
    '''
        a method to upload an image to the server
    '''
    commPage = Communities.query.filter_by(id = commID).first().page
    if current_user.is_in_this_community(commPage) :    
        if request.method == 'POST':
            aFile = request.files['photo']
            if aFile and allowed_file(aFile.filename):
                filename = secure_filename(aFile.filename)
                aFile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                commPage.background_image = filename
                alchemyDB.session.commit()
                flash("Uploaded new community image!")
            else :
                flash("Improper file type or file missing!")
    else :
        flash("You are not in that community!")
    return redirect(url_for('display_community', commID = commID))



def getListOfEntriesSortedByAmountThisEntrySupports(community):
    '''
        Given a community, return a list of all entries sorted
        by the number of entries that support each entry.
    '''
    allSupportedEntries = {}
    for commEntEnt in community.srcOutRelations_in_this_community.all() :        
        srcOut = commEntEnt.srcOutRelation
        if srcOut.confirmedRelType.resp_rel_type.name == 'supports' and srcOut.confirmedRelType.is_reversed:
            if allSupportedEntries.get(srcOut.output) == None :
                allSupportedEntries[srcOut.output] = 1
            else :
                allSupportedEntries[srcOut.output] += 1            
            if allSupportedEntries.get(srcOut.source) == None :
                allSupportedEntries[srcOut.source] = 0                
        elif srcOut.confirmedRelType.resp_rel_type.name == 'supports' and not srcOut.confirmedRelType.is_reversed:
            if allSupportedEntries.get(srcOut.source) == None :
                allSupportedEntries[srcOut.source] = 1
            else :
                allSupportedEntries[srcOut.source] += 1
            if allSupportedEntries.get(srcOut.output) == None :
                allSupportedEntries[srcOut.output] = 0
        else :
            if allSupportedEntries.get(srcOut.source) == None :
                allSupportedEntries[srcOut.source] = 0
            if allSupportedEntries.get(srcOut.output) == None :
                allSupportedEntries[srcOut.output] = 0                
    return [(k, allSupportedEntries[k]) for k in sorted(allSupportedEntries, key=allSupportedEntries.get, reverse = True)]


def getListOfEntriesSortedByAmountOfSupport(community):
    '''
        Given a community, return a list of all entries sorted
        by the number of entries that support each entry.
    '''
    allSupportedEntries = {}
    for commEntEnt in community.srcOutRelations_in_this_community.all() :        
        srcOut = commEntEnt.srcOutRelation
        if srcOut.confirmedRelType.resp_rel_type.name == 'supports' and not srcOut.confirmedRelType.is_reversed:
            if allSupportedEntries.get(srcOut.output) == None :
                allSupportedEntries[srcOut.output] = 1
            else :
                allSupportedEntries[srcOut.output] += 1
            if allSupportedEntries.get(srcOut.source) == None :
                allSupportedEntries[srcOut.source] = 0
        elif srcOut.confirmedRelType.resp_rel_type.name == 'supports' and srcOut.confirmedRelType.is_reversed:
            if allSupportedEntries.get(srcOut.source) == None :
                allSupportedEntries[srcOut.source] = 1
            else :
                allSupportedEntries[srcOut.source] += 1
            if allSupportedEntries.get(srcOut.output) == None :
                allSupportedEntries[srcOut.output] = 0
        else :
            if allSupportedEntries.get(srcOut.source) == None :
                allSupportedEntries[srcOut.source] = 0
            if allSupportedEntries.get(srcOut.output) == None :
                allSupportedEntries[srcOut.output] = 0
    return [(k, allSupportedEntries[k]) for k in sorted(allSupportedEntries, key=allSupportedEntries.get, reverse = True)]


def entryDescendantPairListToDictList(entSupList):
    '''
        We are printing a list of entries sorted by how much support they have.
        The list is actually a list of pairs of entries and the number of supporting articles.
        We take that list and return a list of dictionaries that describe the entries along with thei
        respective number of supporting articles.
    '''
    dictList = []
    for entSupPair in entSupList :
        aDict = convertEntryObjectTDict(entSupPair[0])
        aDict['num_descendants'] = entSupPair[1]
        dictList.append(aDict)
    return dictList


def entrySupportPairListToDictList(entSupList):
    '''
        We are printing a list of entries sorted by how much support they have.
        The list is actually a list of pairs of entries and the number of supporting articles.
        We take that list and return a list of dictionaries that describe the entries along with thei
        respective number of supporting articles.
    '''
    dictList = []
    for entSupPair in entSupList :
        aDict = convertEntryObjectTDict(entSupPair[0])
        aDict['num_supporters'] = entSupPair[1]
        dictList.append(aDict)
    return dictList

def getCommunityTagStrings(community) :
    '''
        givena  community, we sometimes want to have all the tag strings for that community
    '''
    tagSet = set()
    for srcOut in community.srcOutRelations_in_this_community.all() :
        tagSet = tagSet.union(set([tag.tag for tag in srcOut.srcOutRelation.source.tags] + [tag.tag for tag in srcOut.srcOutRelation.output.tags]))
    return list(tagSet)

def getCommunityTagObjects(community) :
    '''
        given a community, we may want to have a list of all the tag objects in that community
    '''
    tagSet = set()
    for srcOut in community.srcOutRelations_in_this_community.all() :
        tagSet = tagSet.union(set([tag for tag in srcOut.srcOutRelation.source.tags] + [tag for tag in srcOut.srcOutRelation.output.tags]))
    return list(tagSet)
    
def convertCommunityPageToJinjaDict(commPage):
    '''
        takes in a community page and produces a
        dictionary that can be used by Jinja to 
        generate the webpage.  This function also returns a list of entries sorted by 
        the number of articles which support a given entry.
    '''
    tagSet = set()
    for srcOut in commPage.community.srcOutRelations_in_this_community.all() :
        tagSet = tagSet.union(set([tag.tag for tag in srcOut.srcOutRelation.source.tags] + [tag.tag for tag in srcOut.srcOutRelation.output.tags]))
    entries = entrySupportPairListToDictList(getListOfEntriesSortedByAmountOfSupport(commPage.community))       
    thePageDict = {}
    thePageDict['comm_name'] = "" if commPage.community_name == None else commPage.community_name 
    thePageDict['banner_text'] =  "" if commPage.banner_text == None else commPage.banner_text 
    thePageDict['eplanation_text'] = "" if commPage.eplanation_text == None else commPage.eplanation_text
    thePageDict['background_image'] = commPage.background_image#os.path.join(app.config['UPLOAD_FOLDER'], commPage.background_image) if commPage.background_image is not None else None
    thePageDict['isUserInComm'] =  current_user in [x.user for x in commPage.community.users_in_this_community]
    thePageDict['entries'] = entries
    thePageDict['relationType'] =  commPage.community.srcOutRelations_in_this_community.first().srcOutRelation.confirmedRelType.resp_rel_type.descriptor
    thePageDict['isReversed'] =  commPage.community.srcOutRelations_in_this_community.first().srcOutRelation.confirmedRelType.is_reversed
    thePageDict['dateCreated'] =  str(commPage.community.date_created)[:10]
    thePageDict['users'] =  [userCommRel.user.user_name for userCommRel in commPage.community.users_in_this_community.all()]
    thePageDict['usersAndIDs'] = [{'name':userCommRel.user.user_name, 'id':userCommRel.user.id} for userCommRel in commPage.community.users_in_this_community.all()]
    thePageDict['tags'] = ", ".join(list(tagSet))
    thePageDict['commPageID'] = commPage.id
    thePageDict['commID'] = commPage.community.id
    return thePageDict


@app.route('/images/<filename>')
@login_required
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)       



@app.route('/display_community/<commID>/', methods = ['GET', 'POST'])
def display_community(commID):
    '''
        Displays a community's homepage.
    '''
    if len(Communities.query.filter_by(id = commID).first().srcOutRelations_in_this_community.all()) == 0:
        flash("That Community is Empty!")
        return redirect(url_for("view_latest_posts"))
    commPage = Communities.query.filter_by(id = commID).first().page        
    return render_template('community_page.html', commPageData = convertCommunityPageToJinjaDict(commPage))


def convertCommunityListToJinjaDictList(commList):
    '''
        We need to convert a list of Communities into a dictionary
        list which will be rendered by Jinja.
    '''
    theJinjaList = []
    for comm in commList :        
        tags = getCommunityTagStrings(comm)
        theJinjaList.append({'id': comm.id, 'commName' : comm.community_name, 'date' : comm.date_created, 'numberUsers' : str(len(comm.users_in_this_community.all())), 'numberDocs' : str(2*len(comm.srcOutRelations_in_this_community.all())), 'tags':tags})
    return theJinjaList

@app.route('/your_communities', methods = ['GET', 'POST'])
@login_required
def your_communities():
    '''
        A page that lists your communities
    '''
    commDictList =  convertCommunityListToJinjaDictList([userCommReg.community for userCommReg in current_user.users_communities])
    return render_template("your_communities.html", commList = commDictList)


def convertUpdateListToJsonifiableDictList(updateList):
    '''
        takes in an update list and converts it to a list of dictionaries.
        As of January 2016, we only have community and response notifications, but this can grow to
        include other kinds of notifications.
    '''
    updateJS_list = []
    for update in updateList :
        if update.community is not None : 
            commName = update.community.community_name
            theDate = update.community.date_created
            theID = update.community.id
            updateType = 0
        else :
            commName = None
            pmSenderName = None
        if update.srcOutRel is not None :            
            srcOutName = update.srcOutRel.output.title
            theDate = update.srcOutRel.confirmedRelType.date_of_confirmation
            theID = update.srcOutRel.output.id
            updateType = 1
        else :
            srcOutName = None
            pmSenderName = None
        if update.private_message is not None :
            pmSenderName = update.private_message.sender_user.user_name
            theDate = update.private_message.date_sent
            theID = update.private_message.id
        else :
            commName = None
            srcOutName = None
        updateJS_list.append({'comm' : commName, 'resp' : srcOutName, 'pmSenderName' : pmSenderName, 'date' : theDate, 'type' : updateType, 'id' : theID, 'updateID' : update.id})
    return updateJS_list      

@app.route('/clear_update', methods = ['GET', 'POST'])
def clear_update():
    '''
        After a user has clicked on their update, it is cleared.
    '''
    update_id = request.args.get("updateID", "", type=str)
    anUpdate = UserUpdates.query.filter_by(id = update_id).first()
    alchemyDB.session.delete(anUpdate)
    alchemyDB.session.commit()
    return jsonify({})

@app.route('/_get_user_update', methods = ['GET', 'POST'])
@login_required
def _get_user_update():
    '''
        every time the user refreshes their page or goes to a new page,
        this function is called to update their banner with notifications
        of new article matches and new communities they have joined.
    '''
    if current_user.is_authenticated:
        return jsonify(updates = convertUpdateListToJsonifiableDictList(current_user.updates))
    else :
        return jsonify({})


@app.route('/show_updates/', methods = ['GET', 'POST'])
@login_required
def show_updates():
    '''
        A page to show updates
    '''
    rawUpdates = UserUpdates.query.filter_by(user_id = current_user.id)
    updates = convertUpdateListToJsonifiableDictList(rawUpdates)
    return render_template("view_your_updates.html", updates = updates)

def alertUsersToNewCommunity(srcTrgObj) :
    '''
        Once a new community has been formed, we need to alert the
        users as to the new community.
    '''
    pass

def createNewCommunityGivenSrcTrgtRel(srcTrgObj):
    '''
        Create a new community given the graph containing the 
        srource Target Relation Object.
    '''
    
    aComm = Communities(community_name = srcTrgObj.source.title, date_created = datetime.now())
    alchemyDB.session.add(aComm)
    alchemyDB.session.flush()
    srcTrgObj.source.user_who_created.join_a_community(aComm)
    srcTrgObj.output.user_who_created.join_a_community(aComm)
    alchemyDB.session.flush()
    srcTrgObj.add_this_rel_to_community(aComm)
    sourceUpdate = UserUpdates(user_id = srcTrgObj.source.user_id, community_update = aComm.id, update_date = datetime.now())
    outputUpdate =  UserUpdates(user_id = srcTrgObj.output.user_id, community_update = aComm.id, update_date = datetime.now())
    alchemyDB.session.add(sourceUpdate)
    alchemyDB.session.add(outputUpdate)
    alchemyDB.session.flush()
    commPage = CommunityPage(community_name = srcTrgObj.source.title)
    alchemyDB.session.add(commPage)
    alchemyDB.session.flush()
    aComm.comm_page = commPage.id
    alertUsersToNewCommunity(srcTrgObj)

def createOrUpdateCommunity(srcTrgObj):
    '''
        In the first release, a community is any network of source Target Objects.
        In this function, we first attempt to discover if this new source Target object is part
        of an existing community.  If so, we update the community by adding the srcTrgObj and any
        new users.  If not, then we create a community with just this srcTrgObj.
    '''
    date_of_comm_update = datetime.now()
    commList = Communities.query.all()
    for comm in commList :
        for commEntEnt in comm.srcOutRelations_in_this_community :
            srcOut =commEntEnt.srcOutRelation
            if srcOut.source == srcTrgObj.source or srcOut.source == srcTrgObj.output or srcOut.output == srcTrgObj.source or srcOut.output == srcTrgObj.output :  
                commEntToEnt = CommunityEntryToEntryRelation(community_id = comm.id, date_rel_was_added = date_of_comm_update, relationship_id = srcTrgObj.id)
                alchemyDB.session.add(commEntToEnt)
                if srcTrgObj.source.user_id != srcTrgObj.output.user_id :
                    sourceUpdate = UserUpdates(user_id = srcTrgObj.source.user_id, community_update = comm.id, update_date = date_of_comm_update)
                    outputUpdate =  UserUpdates(user_id = srcTrgObj.output.user_id, community_update = comm.id, update_date = date_of_comm_update)
                    alchemyDB.session.add(sourceUpdate)
                    alchemyDB.session.add(outputUpdate)
                    srcTrgObj.source.user_who_created.join_a_community(comm)
                    srcTrgObj.output.user_who_created.join_a_community(comm)
                else :
                    sourceUpdate = UserUpdates(user_id = srcTrgObj.source.user_id, community_update = comm.id, update_date = date_of_comm_update)
                    alchemyDB.session.add(sourceUpdate)
                alchemyDB.session.commit()
                return
    createNewCommunityGivenSrcTrgtRel(srcTrgObj)
    alchemyDB.session.commit()

def doesTheGraphFormA_NewCommunity(srcTrgtObj):
    '''
        gets the graph that contains the srcTarget object.  This graph is formed by following the relationship
        types (such as A supports B).
    '''    
    return True



def checkCommunityStatus(srcTrgtObj):
    '''
        once a relationship has been successfully voted on and confirmed, we need to know 
        if this new relation creates or updates a community.
        
        1. check if this relation is part of a graph.
            -If it is, update the graph.
                -If the graph is part of a community, register the new relationship
                with the community along with the users.
                -If the graph is not part of a community, check if the new, updated graph forms a community.
                    -If the new graph forms a community, create it and add the graph to the new community along with all the users
                    -If it doesn't form a community, then do nothing.
    '''
    if not srcTrgtObj.communities_this_relation_is_a_part_of.all() :
        if doesTheGraphFormA_NewCommunity(srcTrgtObj) :
            createOrUpdateCommunity(srcTrgtObj)
    

def checkIfVoteThresholdIsReached(srcTrgtObj) :
    '''
        This function checks to see if a particular srcTargt object has had enough votes
        of any one type to be considered successfully compared.
    '''
    relTypes = ResponseRelationTypes.query.all()
    relTypeDict = {}
    for relType in relTypes :
        relTypeDict[(relType, True)] = 0
        relTypeDict[(relType, False)] = 0
    for vote in srcTrgtObj.votes_for_this_rel :
        if vote.is_reversed :
            relTypeDict[(vote.resp_rel_type, True)] += 1
        else :
            relTypeDict[(vote.resp_rel_type, False)] += 1
        for truth in [True, False] :    
            if  relTypeDict[(vote.resp_rel_type, truth)] > successful_relationship_type_vote_threshold :                   
                srcTrgtObj.needs_processing = False
                typeConfirmation = ConfirmedSrcOutRelType(relationship_type  = vote.resp_rel_type.id, number_of_votes = relTypeDict[vote.resp_rel_type, truth], date_of_confirmation = datetime.now(), is_reversed = truth)
                alchemyDB.session.add(typeConfirmation) 
                if vote.resp_rel_type.name != "no relation" :
                    newSrcUpdate = UserUpdates(user_id = srcTrgtObj.source.user_id,response_update = srcTrgtObj.id, update_date = datetime.now())
                    newOutUpdate = UserUpdates(user_id = srcTrgtObj.output.user_id,response_update = srcTrgtObj.id, update_date = datetime.now())                                                         
                    alchemyDB.session.add(newSrcUpdate)
                    alchemyDB.session.add(newOutUpdate)
                    alchemyDB.session.flush()
                    srcTrgtObj.confirmed_relationship_type = typeConfirmation.id                    
                    checkCommunityStatus(srcTrgtObj)
                alchemyDB.session.commit()
                return True
    return False


@app.route('/save_relation_vote/<srcTrgtID>', methods = ['GET', 'POST'])
@login_required
def save_relation_vote(srcTrgtID):
    '''
        this saves the relation type vote
    '''
    checked = request.form['arComp']
    isReversed = request.form['isReversed']
    srcOutObj = SourceToOutputRelation.query.filter(SourceToOutputRelation.id == srcTrgtID).first()
    srcOutObj.number_of_votes += 1        
    aVote = SourceToOutputRelationTypeVote(source_output_articles = srcTrgtID,
                                            user_who_cast_vote = current_user.id,
                                            relationship_type = checked,
                                            is_reversed = isReversed,
                                            vote_date = datetime.now())
    alchemyDB.session.add(aVote)
    alchemyDB.session.commit()
    checkIfVoteThresholdIsReached(srcOutObj)       
    flash("Thank you for comparing those articles.  Your are helping the users to establish a community.")
    return redirect(url_for('index'))



def signal_handler(signal, frame):
    print("Admin pressed Ctrl-C")
    with app.test_request_context():
        resp = make_response(render_template('show_entries.html'))
        resp.set_cookie('sessionID', '', expires=0)
    sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)



    signal.signal(signal.SIGINT, signal_handler)



def convertTagQueryIntoTagString(query):
    '''
        tags are stored dynamically as a query, so you have to convert that into
        the actual tag objects and then into a string of tags
    '''
    return " ".join([a.tag for a in query.all()])

def baseEntryToDict(EntryObject):
    '''
        Takes an entry and converts
    '''
    tags = convertTagQueryIntoTagString(EntryObject.tags)
    tagList = tags.split(" ")
    return {'id' : EntryObject.id, 'title':EntryObject.title, 'text':EntryObject.text[:50], 'body_html' : EntryObject.body_html, 'tags':tags, 'tagList' : tagList, 'date_posted' : EntryObject.date_posted, 'user_name' : EntryObject.user_who_created.user_name, 'userID':EntryObject.user_who_created.id}


def inputOrOutputToDict(origEntry, input = None, output = None):
    '''
        Takes an entry and converts
    '''
    
    
    if input :
        srcTargID = SourceToOutputRelation.query.filter(and_(SourceToOutputRelation.source_article == input.id, SourceToOutputRelation.output_article == origEntry.id)).first().id   
        entry = input
    else :
        srcTargID = SourceToOutputRelation.query.filter(and_(SourceToOutputRelation.source_article == origEntry.id, SourceToOutputRelation.output_article == output.id)).first().id    
        entry = output
    tags = convertTagQueryIntoTagString(entry.tags)
    tagList = tags.split(" ")
    return {'id' : entry.id, 'title':entry.title, 'text':entry.text[:50], 'body_html' : entry.body_html, 'tags':tags, 'tagList' : tagList, 'date_posted' : entry.date_posted, 'user_name' : entry.user_who_created.user_name, 'userID': entry.user_who_created.id, 'srcTargID' : srcTargID}
    
 
def getEntryJsonifiedFromID(EntryID) :
    '''
        Given an entry ID we want to return all th einformation from convertEntryObjectTDict as a jsonified dictionary
    '''
    EntryObject = Entries.query.filter_by(id=EntryID)
    return jsonify(entry = convertEntryObjectTDict(EntryObject))
    
def convertEntryObjectTDict(EntryObject):
    '''
        takes an entry object and turns it into a dictionary with tags as a text string
    '''
    tags = convertTagQueryIntoTagString(EntryObject.tags)
    tagList = tags.split(" ")
    inputs = [inputOrOutputToDict(EntryObject, input = x.source) for x in EntryObject.source_entries.all()]
    outputs = [inputOrOutputToDict(EntryObject, output = x.output) for x in EntryObject.output_entries.all()]
    return {'id' : EntryObject.id, 'title':EntryObject.title, 'text':EntryObject.text[:50], 'body_html' : EntryObject.body_html, 'tags':tags, 'tagList' : tagList, 'date_posted' : EntryObject.date_posted, 'date_posted_current_timezone': get_localzone().localize(EntryObject.date_posted), 'user_name' : EntryObject.user_who_created.user_name, 'userID':EntryObject.user_who_created.id, 'inputs': inputs, 'outputs':outputs}


def convertEntryListToDictList(entryList):
    '''
        convert an Entry object list to a 
    '''
    dictList = []
    for ent in entryList :
        dictList.append(convertEntryObjectTDict(ent))
    return dictList

@app.route('/view_latest', methods = ['GET', 'POST'])
def view_latest_posts():
    '''
        shows the latest posts, so a list of all posts in id descending order
    '''
    page = request.args.get('page', 1, type=int)
    pagination = Entries.query.order_by(Entries.date_posted.desc()).paginate(page,
                                                                             per_page=current_app.config['CANON_POSTS_PER_PAGE'],
                                                                             error_out = False)
    entries = convertEntryListToDictList(pagination.items)
    return render_template('show_latest_entries2.html', entries=entries, pagination = pagination)


#Custom
#=========

@app.route('/delete_entry/<id>', methods = ['GET'])
@login_required
@mod_required
def delete_entry(id):
    Entries.query.filter_by(id=id).delete()
    flash("Entry deleted.")
    return redirect(url_for('index'))


@app.route('/write_response/<id>', methods = ['GET', 'POST'])
@login_required
def write_response(id):
    '''
        write response to article
    '''
    origObj = Entries.query.filter(Entries.id == id).first()
    origTags = [x.tag for x in origObj.tags]
    original_post = dict(title=origObj.title, text=origObj.text, body_html=origObj.body_html, user_name = origObj.user_who_created.user_name, date_posted = origObj.date_posted, date_posted_current_timezone = get_localzone().localize(origObj.date_posted), tags = origTags, id=origObj.id, user_id=origObj.user_id)
    userLibrary = [a.library_entry for a in current_user.user_library]
    userLibrary.extend(current_user.users_entries)
    userLibEntries = convertEntryListToDictList(userLibrary)
    form = NewEntry()
    if not current_user.email_confirmed and not testAndDebug:
        flash("You need to confirm your email to post a new entry!")
        return redirect(url_for('index'))
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit() :    
        tags = form.tags.data
        tagList = splitA_TagStringByCommaAndSpace(tags)
        tagObjectList = addNewTagsFromList(tagList)
        anEntry = Entries(title = form.title.data,text = form.text.data, user_id = current_user.id)          
        alchemyDB.session.add(anEntry)
        alchemyDB.session.flush()        
        anEntry.tags.extend(tagObjectList)     
        print(form.srcLibEntries.data)
        create_src_to_output_rel(form.srcLibEntries.data, anEntry.id)      
        alchemyDB.session.commit()
        flash('New entry was successfully posted!')        
        return redirect(url_for('index'))
    return render_template('write_response.html', original_post=original_post, userLib = userLibEntries, form = form) 
      
@app.route('/save_response/<original_id>', methods = ['GET', 'POST'])
@login_required
def save_response(original_id):
    '''
        saves the response to an article
    '''        
    newEntry = Entries(title = request.form['title'],
                       text = request.form['text'],
                       user_id = current_user.id,
                       date_posted = datetime.now())
    alchemyDB.session.add(newEntry) # @UndefinedVariable
    tags = splitA_TagStringByCommaAndSpace(request.form['tags'])
    tagObjectList = addNewTagsFromList(tags)
    newEntry.tags.extend(tagObjectList)
    alchemyDB.session.flush()  # @UndefinedVariable    
    create_src_to_output_rel(request.form['srcLibArticles'].strip() + " " + original_id, newEntry.id)    
    alchemyDB.session.commit()  # @UndefinedVariable
    flash('Excellent work!  Your response was successfully saved and will be assessed shortly.')
    return redirect(url_for('view_latest_posts'))
      
      

def create_src_to_output_rel(srcLibArticles, newArticleID):
    '''
        given the original id article (ie the id of the target) and a space separated string
        of source ids, this method will create within the databas all the source to target relation entries.
        If the length of the srcLibArticles string is zero, the method does nothing.
    '''    
    if len(srcLibArticles) != 0 :
        theSrcArts = (srcLibArticles.strip()).split(" ")           
        for art in theSrcArts :
            src = int(art)
            inOutRel = SourceToOutputRelation(source_article = src, output_article = newArticleID, date_related = datetime.now())
            alchemyDB.session.add(inOutRel) # @UndefinedVariable


def splitA_TagStringByCommaAndSpace(aTagString):
    '''
        takes in a tag string and splits it by spaces and commas, stripping off any commas
        and spaces and returns a list of tags.
    '''    
    if aTagString == "" :
        return []
    splitTags = re.split("\r|\n| |\,|\.|\<|\>", aTagString)
    splitTags = filter(lambda z : z!='', splitTags)
    return splitTags



def get_or_create(session, model, **kwargs):
    '''
        This function lets us add an item to a table only if
        it is not already there.
    '''
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


def addNewTagsFromList(tagList):
    '''
        creates new tags, and adds them to the tag table if they aren't there already
        Returns the list of tags as objects in the database
    '''
    tagObjectList = []    
    for aTag in tagList :
        tagObjectList.append(get_or_create(alchemyDB.session, Tags, tag=aTag))
    return tagObjectList
    
def createTagArticleRelation(tagObjectList, entry_id, entryObject):
    '''
        adds tags to an entry
    '''
    theEntry = Entries.query.filter(Entries.id == entry_id).first()
    for tagObject in tagObjectList :        
        theEntry.tags.append(tagObject)


def getFilterCommunitiesFilteredOnTagsQuery(tags):       
    from sqlalchemy.orm import aliased
    
    '''
    q = Communities.query.order_by(Communities.date_created.desc()).\
         join(CommunityEntryToEntryRelation).\
         join(SourceToOutputRelation).\
         join(Entries.source_entries, Entries.output_entries).\
         join(original_tag_registration).\
         join(Tags).\
         filter(Tags.tag == tags[0]) 
    '''
    q = SourceToOutputRelation.query.join(Entries.source_entries, Entries.output_entries)
         
    print(q.all())
    '''
        
         join(original_tag_registration).\
         join(Tags).\
         filter(Tags.tag == tags[0]) 
    '''
    
    tag_alias = aliased(Tags)
    tag_entry_reg_alias = aliased(original_tag_registration)
    i = 0
    for tag in tags[1:]:
        alias1 = aliased(Tags)
        alias2 = aliased(original_tag_registration)
        q = q.join(alias2, Entries.id == alias2.c.entry_id).\
              filter(alias1.id == alias2.c.tag_id).\
              filter(alias1.tag == tag)
        i += 1 
    print(q.all())
    return q        
        

def getAllCommunitiesGivenTags(tags):
    '''
        gets all articles given tags, returns a list of entries
    '''    

    if tags == '' :
            return (Communities.query.order_by(Entries.date_posted.desc()))             
    tagList = splitA_TagStringByCommaAndSpace(tags)
    query = getFilterCommunitiesFilteredOnTagsQuery(tagList)
    return query
        

@app.route('/show_filtered_communities', methods = ['GET', 'POST'])
def filter_communities():
    '''
        will show articles filtered down to include only those with given tags
    '''
    commList = getAllCommunitiesGivenTags(request.form['tags'])
    print(commList)
    return render_template("latest_communities.html", commList = commDictList)


@app.route('/show_filtered_entries', methods = ['GET', 'POST'])
def filter_entries():
    '''
        will show articles filtered down to include only those with given tags
    '''
    entries = getAllArticlesGivenTags(request.form['tags'])
    return index(entries)


def getAllArticlesGivenTags(tags):
    '''
        gets all articles given tags, returns a list of entries
    '''    

    if tags == '' :
            return (Entries.query.order_by(Entries.date_posted.desc()))             
    tagList = splitA_TagStringByCommaAndSpace(tags)
    query = getFilterEntriesFilteredOnTagsQuery(tagList)
    return query
    


def getFilterEntriesFilteredOnTagsQuery(tags):       
    from sqlalchemy.orm import aliased
    
    q = Entries.query.order_by(Entries.date_posted.desc()).\
         join(original_tag_registration).\
         join(Tags).\
         filter(Tags.tag == tags[0])    
    tag_alias = aliased(Tags)
    tag_entry_reg_alias = aliased(original_tag_registration)
    i = 0
    for tag in tags[1:]:
        alias1 = aliased(Tags)
        alias2 = aliased(original_tag_registration)
        q = q.join(alias2, Entries.id == alias2.c.entry_id).\
              filter(alias1.id == alias2.c.tag_id).\
              filter(alias1.tag == tag)
        i += 1   
    return q
    
    
def getAllUsersLibraryArticlesGivenTags(tags):
    '''
        gets all the users library articles that are tagged with any of the input tags
        tags is a araw tag string from the webpage input box
    '''
    if tags == '' :
        libObjects = [a.library_entry for a in current_user.user_library.all()]
        libObjects.extend(current_user.users_entries)        
    else :
        tagStringList = splitA_TagStringByCommaAndSpace(tags)
        unfLibObj = [a.library_entry for a in current_user.user_library]
        unfLibObj.extend(current_user.users_entries)
        libObjects = []
        for libObj in unfLibObj :            
            if(set([b.tag for b in libObj.tags]) & set(tagStringList)):
                libObjects.append(libObj)
    return libObjects


@app.route('/_filter_lib_articles', methods = ['GET', 'POST'])
@login_required
def filter_lib_articles():
    '''
        allows a user to filter library articles on tags when creating a response article
    '''
    tags = request.args.get("tags", "", type=str)
    savedIDs = request.args.get("savedLibArticleIds", "", type=str)
    libArts = getAllUsersLibraryArticlesGivenTags(tags)
    alreadySavedReadyForJsonify = convertEntriesListToJsonifyableDictList(retrieveArticlesGivenIDList(savedIDs))
    return jsonify(libArticles = convertEntriesListToJsonifyableDictList(libArts), entriesForSavedList = alreadySavedReadyForJsonify)

@app.route('/filter_view_library_entries', methods = ['GET', 'POST'])
@login_required
def filter_view_library_entries():
    '''
        this filter's a user's library on tags
    '''
    libArts = getAllUsersLibraryArticlesGivenTags(request.form['tags'])    
    return render_template('view_library.html', entries = convertEntryListToDictList(libArts))

def convertEntriesListToJsonifyableDictList(entryList):
    '''
        you cannot jsonify a list of arbitrary objects, but it seems you can jsonify a list of dictionaries
    '''
    libArtsDictList = []
    for entry in entryList :
        libArtsDictList.append({ 'user_name': entry.user_who_created.user_name, 'user_id': entry.user_who_created.id,'timestamp' : entry.date_posted,  'id' : entry.id, 'title' : entry.title, 'tags':" ".join([a.tag for a in entry.tags.all()]), 'text': entry.text[:50]})
    return libArtsDictList


@app.route('/_get_some_articles', methods = ['GET', 'POST'])
def retrieveAndJsonifyArticlesGivenIDList(idList) : 
    '''
        a one stop shop for ajax calls for a list of articles given a list of article ids.
    '''   
    return jsonify(convertEntriesListToJsonifyableDictList(retrieveArticlesGivenIDList(idList)))


def retrieveArticlesGivenIDList(idListAsString) :
    '''
        given a list of article ids, this function returns a list of Entry model objects.
    '''    
    idList = (idListAsString.strip()).split(" ")
    articles = []
    for entry in Entries.query.filter(Entries.id.in_(idList)) : # @UndefinedVariable :
        articles.append(entry)
    return articles

@app.route('/_save_to_read_history/', methods = ['GET', 'POST'])
@login_required
def save_to_read_history():
    '''
         this is a simple button to save an article to a user's library.
         
         The library will be used to compose two or more articles and build on them when
         creating a new entry.
    '''
    original_id = request.args.get("original_id", "", type=str)
    if not current_user.user_library.filter_by(article_id = original_id).count() : # @UndefinedVariable
        origEntry = Entries.query.filter(Entries.id == original_id).first()
        if not origEntry in current_user.users_entries: 
            readEntry = UsersReadArticles(date_read = datetime.now())            
            readEntry.library_entry = origEntry            
            current_user.user_library.append(readEntry)
            alchemyDB.session.commit()
            returnString = "The original article has been saved to your library."
        else :
            returnString = "You can't add your own articles to your library.  Look for your articles in your profile page."
    else :
        returnString = "This article is already in your library."
    return jsonify(returnString = returnString)
        

@app.route('/your_entries/', methods = ['GET', 'POST'])
@login_required
def your_entries():
    '''
        this is a page to display a user's entries.
    '''
    entryList = current_user.users_entries
    return render_template('view_your_entries.html', entries = convertEntryListToDictList(entryList), user_id = current_user.id)


@app.route('/your_library', methods = ['GET', 'POST'])
@login_required
def view_library():
    '''
        This just lets people look at the articles in their saved library.
    '''
    userLib = current_user.user_library.all()
    entryList = [a.library_entry for a in userLib]
    return render_template('library.html', entries=convertEntryListToDictList(entryList))



@app.route('/assign_moderator/', methods = ['GET', 'POST'])
@admin_required
@login_required
def assign_moderator():
    '''
        administrators can assign a user to be a moderator
    '''
    return render_template("assign_moderator.html")


def convertUserListToDictList(userList):
    '''
        sometimes we want to print a list of users to a template
        and this converts a user list to a nice printable dictionary list.
        
        
    '''
    uDictList = []
    for user in userList :
        uDictList.append({"user_name" : user.user_name, "user_ID": user.id, "date_joined":user.date_joined, "role":user.role.name, "email":user.user_email})
    return uDictList


@app.route('/get_user_for_admin_purposes/', methods = ['GET', 'POST'])
@login_required
def get_user_for_admin_purposes():
    '''
        this is a jquery function tot retun a user id given a search string
        so that the moderator can assign moderator status to the user.
    '''
    userSearchString = request.args.get("user_name_search_string", "", type=str)
    possibleUsers = User.query.filter(User.user_name.contains(userSearchString)).all()
    return jsonify(users = convertUserListToDictList(possibleUsers))


@app.route('/get_user_with_common_communities/', methods = ['GET', 'POST'])
@login_required
def get_user_with_common_communities():
    '''
        this is a jquery function tot retun a user id given a search string
        so that the moderator can assign moderator status to the user.
    '''
    userSearchString = request.args.get("user_name_search_string", "", type=str)
    allSimilarUsers = User.query.filter(User.user_name.contains(userSearchString)).all()
    possibleUsers = []
    for user in allSimilarUsers :
        if usersInCommunityTogether(user) :
            possibleUsers.append(user)
    return jsonify(users = convertUserListToDictList(possibleUsers))


def getSharedCommunities(user1, user2):
    '''
        Given two user, this returns a list of communities that
        the two users are both members of 
    '''
    sharedComms = []
    user2Comms = [x.community for x in user1.users_communities]
    for com in [x.community for x in user1.users_communities] :
        if com in user2Comms :
            sharedComms.append(com)
    return sharedComms
    

@app.route('/set_moderator_status/', methods = ['GET', 'POST'])
@admin_required
@login_required
def set_moderator_status():
    '''
        Allows an administrator to set a user's role to moderator
    '''    
    userID = request.form["selected_user"]
    aUser = User.query.filter_by(id = int(userID)).first()
    aUser.set_moderator_status()
    flash("User " + aUser.user_name + " now has moderator status!")
    return redirect(url_for('assign_moderator'))

@app.route('/mod_deletes_post/<original_id>', methods = ['GET', 'POST'])
@mod_required
def mod_deletes_post(original_id):
    '''
        Moderators can delete posts.  This is the basic function to do that.
    '''
    theEntry = Entries.query.filter_by(id = original_id).first()
    alchemyDB.session.delete(theEntry)
    alchemyDB.session.commit()
    flash("Entry Deleted!")
    return redirect(url_for('view_latest_posts'))

@app.route('/delete_user/', methods = ['GET', 'POST'])
@admin_required
def delete_user():
    '''
        Directs to a page where an admin can delete a user.
    '''
    return render_template("delete_user.html")


@app.route('/admin_deletes_user/', methods = ['GET', 'POST'])
@admin_required
def admin_deletes_user():
    '''
        Allows an administrator to set a user's role to moderator
    '''    
    userID = request.form["selected_user"]
    aUser = User.query.filter_by(id = int(userID)).first()
    aUser.ban_user()
    alchemyDB.session.commit()
    flash("User " + aUser.user_name + " has been banned!")
    return redirect("delete_user")


def privateMessageToDict(pm):
    '''
        convert a private message to a dictionary
    '''
    sender = pm.sender_user
    recipient = pm.recipient_user
    return {"title":pm.title,\
            "text":pm.text.replace('\r', '<p>').replace('\n','<p>'),\
            "sender_name":sender.user_name,\
            "sender_id":sender.id,\
            "recipient_name":recipient.user_name,\
            "date_sent":pm.date_sent,\
            "read_or_not": pm.read_or_not,\
            "message_id":pm.id}

def convertPM_ListToDictList(messages):
    '''
        This converts a list of PrivateMessage objects 
        to a list of dictionaries.
    '''
    dictList = []
    for message in messages :
        dictList.append(privateMessageToDict(message))
    return dictList

@app.route('/messaging_center', methods = ['GET','POST'])
@login_required
def messaging_center():
    '''
        Users can send messages to other users in their 
        communities.  This page allows them to do that.
    '''
    usersComms = [x.community for x in current_user.users_communities]
    users = set()
    for comm in usersComms :
        for srcOut in  [x.srcOutRelation for x in comm.srcOutRelations_in_this_community] :
            users.add(srcOut.source.user_who_created.user_name)
            users.add(srcOut.output.user_who_created.user_name)
    messages = (current_user.received_private_messages.all())
    messages.sort(key=lambda x: x.date_sent, reverse=True)    
    return render_template("user-private-messages.html", users = (", ".join(list(users))).strip(","), messages = convertPM_ListToDictList(messages))



@app.route('/compose_send_private_message/<recipientID>', methods = ['GET','POST'])
@login_required
def compose_send_private_message(recipientID):
    '''
        sends a private message
    '''
    form = NewPrivateMessage()
    recipient = User.query.filter_by(id = recipientID).first()
    entryObjList = [a.library_entry for a in current_user.user_library.all()]  
    entryObjList.extend(current_user.users_entries)
    userLibEntries = convertEntryListToDictList(entryObjList)
    if form.validate_on_submit() :                    
        title = form.title.data
        text = form.text.data            
        attachments = form.srcLibEntries.data
        newPM = PrivateMessage(title = title, text = text, sender = current_user.id, recipient = recipientID)
        alchemyDB.session.add(newPM)            
        for attachment in attachments :
            newAtt = PM_Attachments(entry_id = attachment)
            alchemyDB.session.add(newAtt)
        alchemyDB.session.commit()
        flash("Your message has been sent!")        
        return redirect("messaging_center")        
    return render_template("send_private_message.html", form = form, recipientID = recipientID, recipientName = recipient.user_name, userLib = userLibEntries)


@app.route('/create_private_message/', methods = ['GET', 'POST'])
@login_required
def create_private_message():
    '''
        A user can send a private message to another
        user who is in their community or communities.
    '''
    recipientID = request.form["selected_user"] 
    recipient = User.query.filter_by(id = recipientID).first()
    if sendPM_PermissionsAreMet(recipient) :        
        return redirect(url_for("compose_send_private_message", recipientID = recipientID))
    else :
        flash("You don't have permissions to message that user!")   
        return redirect("messaging_center")


def usersInCommunityTogether(recipient) :
    '''    
        If a user and recipient are in the share a community return True, else False
    '''
    recipientComms = [x.community for x in recipient.users_communities.all()]
    for comm in [x.community for x in current_user.users_communities.all()] :        
        if comm in recipientComms :
            return True
    return False


def sendPM_PermissionsAreMet(recipient) :
    '''
        When a user sends private messages to another user,
        we need to check that the permissions are met.  For instance,
        if a sender has banned a participant, this function returns False.
    '''   
    if (usersInCommunityTogether(recipient) or current_user.is_moderator or current_user.is_administrator) : 
        return current_user.canPM_Recipient(recipient)
    return False

@app.route('/send_private_message/', methods = ['GET', 'POST'])
@login_required
def send_private_message():
    '''
        this function "sends" the private message which is to say that
        a private message is created with a sender and recipient.
    '''
    form = NewPrivateMessage()
    recipientID = form.recipient_ID.data
    if form.validate_on_submit() and sendPM_PermissionsAreMet(User.query.filter_by(id = form.recipient_ID.data).first()):
        recipientID = request.form["recipientID"]
        title = request.form["title"]
        text = request.form["text"]
        attachments = request.form["srcLibArticles"]    
        newPM = PrivateMessage(title = title, text = text, sender = current_user.id, recipient = recipientID)
        alchemyDB.session.add(newPM)
        for attachment in attachments :
            newAtt = PM_Attachments(entry_id = attachment)
            alchemyDB.session.add(newAtt)
        alchemyDB.session.commit()
        flash("Your message has been sent!")        
        return redirect("messaging_center")
    return render_template("send_private_message.html")

def getReplyPM_Chain(message):
    '''
        given a message, this retrieves the email chain and
        returns a list of private messages sorted as to reflect
        the email chain (the first in the chain is the first in the list).
    '''
    messageList = []
    currentMessage = message
    iters = 1
    while currentMessage.chain_parent.first() is not None and iters < 10 :
        iters += 1        
        currentMessage = currentMessage.chain_parent.first().parent_message
        messageList.append(currentMessage)
    #messageList.reverse()
    return messageList

@app.route('/read_private_message/<message_id>', methods = ['GET', 'POST'])
@login_required
def read_private_message(message_id):
    '''
        This allows users to read a private messge    
    '''
    
    message = PrivateMessage.query.filter(and_(PrivateMessage.id==message_id, PrivateMessage.recipient==current_user.id)).first()
    if message is not None :
        message.read_or_not = True
        alchemyDB.session.commit()
        sender = User.query.filter_by(id=message.sender_user.id).first()
        sharedCommunities  = [x.community_name for x in getSharedCommunities(current_user, sender)]  
        recipientUser = message.sender_user   
        if sendPM_PermissionsAreMet(recipientUser) :      
            form = NewPrivateMessage()              
            if form.validate_on_submit():
                recipientID = recipientUser.id        
                title = "re : " + message.title
                text = form.text.data
                attachments = form.srcLibEntries.data
                newPM = PrivateMessage(title = title, text = text, sender = current_user.id, recipient = recipientID)
                alchemyDB.session.flush()
                alchemyDB.session.add(newPM)
                alchemyDB.session.flush()
                newReplyLink = PrivateMessageReplyLink(parentMessage = message_id, childMessage = newPM.id)
                alchemyDB.session.add(newReplyLink)
                for attachment in attachments :
                    newAtt = PM_Attachments(entry_id = attachment)
                    alchemyDB.session.add(newAtt)
                alchemyDB.session.commit()
                flash("Your reply has been sent!") 
                return redirect("messaging_center")
            return render_template("read_private_message.html", form = form, message = privateMessageToDict(message), comms = sharedCommunities, replyChain = convertPM_ListToDictList([message] + getReplyPM_Chain(message)), permissions_met = sendPM_PermissionsAreMet(sender))
        else :
            flash("You don't have permissions to private message this user!  They must have blocked you while you were crafting your response.  Sorry for the inconvenience!")
        return redirect("messaging_center")           
        
    else :
        return redirect("messaging_center")

@app.route("/block_user_pm/<sender_id>", methods = ['GET', 'POST'])
@login_required
def block_user_pm(sender_id):
    '''
        When viewing any private message a user is free to block this user
        from that point on.  Blocking is permanent and prevents any communication
        either way between two users.
    '''
    sender = User.query.filter_by(id = sender_id).first()    
    current_user.blockUser(sender) 
    flash("Blocked user : " + sender.user_name + ".  You will not be able to contact this user and they cannot contact you.")
    return redirect("messaging_center")


"""
@app.route("/reply_to_private_message/<message_id>", methods = ['GET','POST'])
@login_required
def reply_to_private_message(message_id):
    '''
        When a user gets a message, they can reply to it
        using this function.
        This is much like sending private message but attempts to keep the message chain.
    '''    
    orig_message = PrivateMessage.query.filter_by(id=message_id).first()    
    recipientUser = orig_message.sender_user    
    form = NewPrivateMessage()
    sender = User.query.filter_by(id=message.sender_user.id).first()
    if sendPM_PermissionsAreMet(recipientUser) 
        if form.validate_on_submit():
            recipientID = recipientUser.id        
            title = "re : " + orig_message.title
            text = request.form["text"]
            attachments = request.form["srcLibArticles"]    
            newPM = PrivateMessage(title = title, text = text, sender = current_user.id, recipient = recipientID)
            alchemyDB.session.flush()
            alchemyDB.session.add(newPM)
            alchemyDB.session.flush()
            newReplyLink = PrivateMessageReplyLink(parentMessage = message_id, childMessage = newPM.id)
            alchemyDB.session.add(newReplyLink)
            for attachment in attachments :
                newAtt = PM_Attachments(entry_id = attachment)
                alchemyDB.session.add(newAtt)
            alchemyDB.session.commit()
            flash("Your reply has been sent!")
        sharedCommunities  = [x.community_name for x in getSharedCommunities(current_user, sender)] 
        return render_template("read_private_message.html", message = privateMessageToDict(orig_message), comms = sharedCommunities, replyChain = convertPM_ListToDictList(getReplyPM_Chain(message)), permissions_met = sendPM_PermissionsAreMet(sender))
    else :
        flash("You don't have permissions to private message this user!  They must have blocked you while you were crafting your response.  Sorry for the inconvenience!")
    return redirect("messaging_center")
 """

def send_async_email(app, msg):
    '''
        So that send email does not block while sending the email
        we have an asynchronous email sender function
    '''
    with app.app_context():
        mail.send(msg)
 
def send_email(to, subject, template, **kwargs):
    '''
        a function to send email to users
    '''   
    msg = Message(app.config['CANONWORKS_MAIL_SUBJECT_PREFIX'] + subject,
                  sender = app.config['CANONWORKS_ADMIN'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)    
    thr =  Thread(target=send_async_email, args=[app,msg])
    thr.start()
    return thr


@app.route('/reset_password/<token>', methods = ['GET', 'POST'])
def reset_password(token):
    '''
        This function helps people reset their password if they forget it.
    
    '''    
    s = Serializer(current_app.config['SECRET_KEY'])
    try :
        data = s.loads(token)
    except :
        flash("Invalid Token!")
        return redirect(url_for('auth.login'))
    userID = data.get('confirm')
    aUser = User.query.filter_by(id = userID).first()       
    form = ResetPassword()
    if aUser : 
        if form.validate_on_submit():            
            aUser.user_pass =  generate_password_hash(form.new_password.data)  
            alchemyDB.session.commit()          
            flash('Your password has been reset.')                
            flash('You can now login.')
            return redirect(url_for('auth.login'))
        return render_template('auth/reset_password.html', form = form)
    else :
        flash("Invalid token!  No such user!")
    return redirect(url_for('auth.login'))
    
    
    



@app.route('/forgot_password', methods = ['GET', 'POST'])
def forgot_password():
    '''
        a user might forget their password and this helps them
        reset their password.
    '''
    form = ForgotPassword()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email = form.email.data).first()
        if user :
            token = user.generate_confirmation_token()
            send_email(user.user_email, "Password Reset", 'auth/email/reset_password', user=user,token=token)
            flash('A password reset email has been sent to that address.')
        else :
            flash("No user with that email!")            
            return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form = form)



@app.route('/change_email_address/<token>', methods = ['GET', 'POST'])
@login_required
def change_email_address(token):
    if current_user.change_email(token) :
        flash("You have successfully changed your email address.")
    else :
        flash("Invalid token!  Your email address has not been changed!")        
    return redirect('user_profile')


@app.route('/change_email', methods = ['GET', 'POST'])
@login_required
def change_email():
    '''
        allows users to change their email address
    '''
    form = ChangeEmail()
    if form.validate_on_submit() :
        newEmail = form.email.data
        token = current_user.generate_email_change_token(newEmail)
        send_email(newEmail, 'Email Address Change', 'auth/email/email_address_change', user = current_user, token = token)
        flash('A confirmation email has been sent to the new address.  Please use it to change your address')
        return redirect('user_profile')
    return render_template('auth/change_email.html', form = form)


@app.route('/public_user_page/<userID>', methods=['GET', 'POST'])
def public_user_page(userID):
    '''
        Users need a way to display their public information about themselves,
        we build that page here.
    '''
    aUser = User.query.filter_by(id = userID).first()
    entries = (Entries.query.filter_by(user_id=userID).all())
    entries.sort(key = lambda x : x.date_posted, reverse=True)
    communities = [x.community for x in aUser.users_communities]
    sharedComms = []
    if current_user.is_authenticated and aUser !=current_user :
        sharedComms = getSharedCommunities(current_user, aUser)            
    return render_template("user-public-profile.html", user = convertUserToJinjaDict(aUser))


@app.route('/ban_user_from_user_page/<userID>', methods =['GET'])
@mod_required
def ban_user_from_user_page(userID):

    banned_role_id = Roles.query.filter_by(name="Banned").first().id
    aUser =  User.query.filter_by(id=int(userID)).first()
    # User.query.filter_by(id=int(userID)).update({"role_id": banned_role_id})
    aUser.role_id = banned_role_id
    alchemyDB.session.commit()
    flash("User has been banned!")

    # aUser.ban_user()
    # aUser.role = Roles.query.filter_by(name="Banned").first()
    # alchemyDB.session.commit()
    # return redirect("delete_user")
    return redirect(url_for('index'))

@app.route('/make_user_mod/<userID>', methods =['GET'])
@admin_required
def make_user_mod(userID):

    mod_role_id = Roles.query.filter_by(name="Moderator").first().id

    aUser =  User.query.filter_by(id=int(userID)).first()
    aUser.role_id = mod_role_id
    alchemyDB.session.commit()
    flash("User has been graduated to moderator!")

    return redirect(url_for('index'))


@app.route('/send_private_message_from_user_page/<userID>', methods = ['GET', 'POST'])
def send_private_message_from_user_page(userID):
    '''
        Users who share communities can send a private message via a link
        in the other user's public page.
    '''
    recipientID = userID
    recipient = User.query.filter_by(id = recipientID).first()
    if sendPM_PermissionsAreMet(User.query.filter_by(id = recipientID).first()) :
        #return render_template("send_private_message.html", recipientID = recipientID, recipientName = recipient.user_name)
        return redirect(url_for('compose_send_private_message', recipientID = recipientID))
    else :
        flash("You don't have permissions to message that user!")
        return redirect("messaging_center")
    


if __name__ == '__main__':
    
    args = sys.argv
    if len(args) != 1 :
        print(args[1])
        shell = (args[1] == 'shell')
        debug = (args[1] == '1')
    else :
        shell = False
        debug = False
    app.debug = debug
    if not shell :        
        app.run(threaded = True)
    else :
        manager.run()

    
   

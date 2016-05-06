'''
Created on Nov 26, 2014

@author: Ben
'''
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import backref
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import and_
from datetime import date, datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach


allowed_html_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong',
                        'ul', 'h1', 'h2', 'h3', 'p']

alchemyDB = SQLAlchemy()


'''
    a table to store which tags have been given to which entries by the 
    users who created that entry.
'''


original_tag_registration = alchemyDB.Table('original_tag_registration',
    alchemyDB.Column('tag_id', alchemyDB.Integer, alchemyDB.ForeignKey('tagTable.id')),
    alchemyDB.Column('entry_id', alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    )

    
class UsersReadArticles(alchemyDB.Model):
    '''
        defines a relationship between a user and an article indicating that 
        a user has saved the article to his library.  The library is meant to be used
        as a collection of articles which a user can reference.  When they create an article
        they have the option to create a response to multiple articles, just like journal articles.
        Also, this adds the extra dimension of a monoidal product over objects (articles).
    '''
    __tablename__ = 'users_read_articles'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    user_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    article_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    date_read = alchemyDB.Column(alchemyDB.DateTime)
    library_entry = alchemyDB.relationship("Entries", backref = "user_assoc")

class UsersAppliedTags(alchemyDB.Model):
    '''
        a association object to handle the tags which a user applies to other people's entries
    '''
    __tablename__ = 'users_applied_tags'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    tag_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('tagTable.id'))
    entry_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    user_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))


'''
    a table that points entries to their corresponding monoidal product
'''
inputsToMonoidalProduct = alchemyDB.Table('monoidal_inputs_registration',
                                          alchemyDB.Column('input', alchemyDB.Integer, alchemyDB.ForeignKey('entries.id')),
                                          alchemyDB.Column('product', alchemyDB.Integer, alchemyDB.ForeignKey('monoidal_input_products.id'))
                                        )
                                          


class monoidalProductOfInputRelation(alchemyDB.Model):
    '''
        This captures the idea that a collection of articles that are identified as inputs
        to an output article should be seen as a monoidal product object.  This relation
        establishes this monoidal product object
    '''
    __tablename__ = 'monoidal_input_products'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    date_created = alchemyDB.Column(alchemyDB.DateTime)
    output_entry = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    input_entries = alchemyDB.relationship('Entries',
                                           secondary = inputsToMonoidalProduct,
                                           backref = alchemyDB.backref('monoidal_products', lazy = 'dynamic'),
                                           lazy  = 'dynamic')


class UserCommunityRelation(alchemyDB.Model):
    '''
        A user can be associated with none, one or more communities.
    '''
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    community_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('communities.id'))
    user_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    date_joined  = alchemyDB.Column(alchemyDB.DateTime)



class CommunityEntryToEntryRelation(alchemyDB.Model):
    '''
        We consider entry relations to be part of a community when it forms.
        We understand that adding a relationship between entries to a community to be like
        adding a morphism to an imprecisely understood category.  The Category is a model, and
        evolves by adding entries and relationships between entries.
        
    '''
    __tablename__ = 'community_entry_entry_relationship'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    community_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('communities.id'))
    date_rel_was_added = alchemyDB.Column(alchemyDB.DateTime)
    relationship_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('sourceToOutputRel.id'))
    
    

class SourceToOutputRelation(alchemyDB.Model):
    '''
        defines a source article to output article relation.  These are articles used as sources for a response.  They are also seen
        as input wires to a morphism box in a monoidal category diagram.
    '''
    __tablename__ =  'sourceToOutputRel'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    source_article = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    output_article = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    needs_processing = alchemyDB.Column(alchemyDB.Boolean, default = True)
    number_of_votes = alchemyDB.Column(alchemyDB.Integer, default = 0)
    votes_for_this_rel = alchemyDB.relationship('SourceToOutputRelationTypeVote',
                                                          backref = alchemyDB.backref('srcOutputObject', lazy = 'joined'),
                                                          lazy = 'dynamic',
                                                          cascade = 'all, delete-orphan')    
    date_related = alchemyDB.Column(alchemyDB.DateTime)
    confirmed_relationship_type = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('confirmedRelationshipType.id'))
    communities_this_relation_is_a_part_of = alchemyDB.relationship('CommunityEntryToEntryRelation',
                                                                    foreign_keys = [CommunityEntryToEntryRelation.relationship_id],
                                                                    backref = alchemyDB.backref('srcOutRelation', lazy = 'joined'),
                                                                    lazy = 'dynamic',
                                                                    cascade = 'all, delete-orphan') 
    response_update = alchemyDB.relationship('UserUpdates', backref = 'srcOutRel', cascade = 'all, delete-orphan')
    
    def add_this_rel_to_community(self, community):
        '''
            Communities are built up by the source output relationships.
            We need to be able to add a srcOutRel to a community and this 
            function does that.
        '''
        if not self.is_this_rel_part_of_a_community(community) :
            aRelCommRegister = CommunityEntryToEntryRelation(community_id = community.id, relationship_id = self.id)
            alchemyDB.session.add(aRelCommRegister)
    
    def is_this_rel_part_of_a_community(self, community):
        '''
            srcOutRels can be part of a community and this function 
            checks if a rel is part of a community.
        '''
        return community.srcOutRelations_in_this_community.filter_by(relationship_id = self.id).first() is not None

class Entries(alchemyDB.Model):
    '''
        defines what an entry is.  This includes text, links, images etc.
    '''
    __tablename__ = 'entries'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    title = alchemyDB.Column(alchemyDB.String(64))
    text = alchemyDB.Column(alchemyDB.String(64))
    body_html = alchemyDB.Column(alchemyDB.Text)
    user_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    date_posted = alchemyDB.Column(alchemyDB.DateTime, index = True, default = datetime.utcnow) 
    tags = alchemyDB.relationship('Tags',
                                  secondary = original_tag_registration,
                                  backref = alchemyDB.backref('relevant_entries', lazy = 'dynamic'),
                                  lazy = 'dynamic')    
    viewer_applied_tags = alchemyDB.relationship('UsersAppliedTags',
                                                 foreign_keys = [UsersAppliedTags.entry_id],
                                                 backref = alchemyDB.backref('entries_with_this_tag_and_user', lazy = 'joined'),
                                                 lazy = 'dynamic',
                                                 cascade = 'all, delete-orphan')
    '''
                                                    
                                                    source_entries = alchemyDB.relationship('SourceToOutputRelation',
                                            primaryjoin="SourceToOutputRelation.output_article==Entries.id",
                                            foreign_keys = [SourceToOutputRelation.output_article],
                                            backref = alchemyDB.backref('output', lazy = 'joined'),
                                            lazy = 'dynamic',
                                            cascade = 'all, delete-orphan')
    output_entries = alchemyDB.relationship('SourceToOutputRelation',                                            
                                            primaryjoin="SourceToOutputRelation.source_article==Entries.id",
                                            foreign_keys = [SourceToOutputRelation.source_article],
                                            backref = alchemyDB.backref('source', lazy = 'joined'),
                                            lazy = 'dynamic',
                                            cascade = 'all, delete-orphan')
                                                 
    '''
    
    source_entries = alchemyDB.relationship('SourceToOutputRelation',
                                            foreign_keys = [SourceToOutputRelation.output_article],
                                            backref = alchemyDB.backref('output', lazy = 'joined'),
                                            lazy = 'dynamic',
                                            cascade = 'all, delete-orphan')
    output_entries = alchemyDB.relationship('SourceToOutputRelation',                                            
                                            foreign_keys = [SourceToOutputRelation.source_article],
                                            backref = alchemyDB.backref('source', lazy = 'joined'),
                                            lazy = 'dynamic',
                                            cascade = 'all, delete-orphan')
        
    users_who_saved_to_lib = alchemyDB.relationship('UsersReadArticles',
                                                    backref = alchemyDB.backref('entry', lazy = 'joined'),
                                                    lazy = 'dynamic',
                                                    cascade = 'all,delete-orphan')
    
    @staticmethod                                  
    def generate_fake(count = 100):
        '''
            generates a fake blog post
        '''
        from random import seed,randint
        import forgery_py
        
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0,user_count - 1)).first()
            p = Entries(text = forgery_py.lorem_ipsum.sentences(randint(1,7)),
                        title = forgery_py.lorem_ipsum.sentences(1),
                        date_posted = forgery_py.date.date(True),
                        user_who_created = u)
            
            alchemyDB.session.add(p)
            alchemyDB.session.commit()
                        
                        
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''
            helps to sanitize blog posts.
        '''              
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_html_tags,strip=True))
        
        
alchemyDB.event.listen(Entries.text, 'set', Entries.on_changed_body)
           
allowed_tag_html_tags = []    

class Tags(alchemyDB.Model):
    '''
        a table to hold unique tags
    '''
    __tablename__ = 'tagTable'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    tag = alchemyDB.Column(alchemyDB.String(64), unique=True)
    entries_with_this_tag = alchemyDB.relationship('Entries',
                                                secondary = original_tag_registration,
                                                backref = alchemyDB.backref('tag', lazy = 'dynamic'),
                                                lazy = 'dynamic') 
    bleached_tag = alchemyDB.Column(alchemyDB.String(64), unique=True)
    
    @staticmethod
    def on_changed_tag(target, value, oldvalue, intitiator):
        '''
            sanitizes tags
        '''
        target.bleached_tag = bleach.linkify(bleach.clean(value, tags=[], strip=True))

alchemyDB.event.listen(Tags.tag, 'set', Tags.on_changed_tag)

    
class Permission :
    '''
        a class containing all the permission types
    '''
    READ_ONLY = 0X01
    WRITE_ARTICLES = 0X04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0X80
    BANNED = 0X02

class Roles(alchemyDB.Model):
    __tablename__ = 'roles'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    name = alchemyDB.Column(alchemyDB.String(64), unique = True)
    default = alchemyDB.Column(alchemyDB.Boolean, default = False, index = True)
    permissions = alchemyDB.Column(alchemyDB.Integer)
    users = alchemyDB.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return '<Role $r>'%self.name
    
    @staticmethod
    def setRolesInDB(app):
        '''
            sets the basic roles in the database
        '''
        roles = {
                 'User' : (Permission.WRITE_ARTICLES, True),
                 'Moderator' : (Permission.WRITE_ARTICLES | Permission.MODERATE_COMMENTS, False),
                 #'Administrator' : (0xff, False),
                 'Administrator' : (Permission.ADMINISTER | Permission.WRITE_ARTICLES |Permission.MODERATE_COMMENTS, False),
                 'SiteOwner' : (Permission.ADMINISTER | Permission.WRITE_ARTICLES |Permission.MODERATE_COMMENTS, False),
                 'Banned' : (Permission.BANNED, False)
                 }
        with app.app_context():
            with alchemyDB.session.no_autoflush:
                for r in roles :
                    role = Roles.query.filter_by(name = r).first()            
                    if role == None :
                        role = Roles(name = r)
                    role.permissions = roles[r][0]
                    role.default = roles[r][1]
                    alchemyDB.session.add(role)
                alchemyDB.session.commit()


class PrivateMessageReplyLink(alchemyDB.Model):
    '''
        This class is meant to creeate email chains
        by defining a link between messages that is 
        quite simple : parent and child.
    '''
    __tablename__ = 'private_message_repaly_link'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    parentMessage = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey("private_message.id"))
    childMessage = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey("private_message.id"))

    
class PrivateMessage(alchemyDB.Model):
    '''
        Users who are in the same community can send private messages.  This
        object embodies those messages
    '''
    def __init__(self, **kwargs) :
        self.read_or_not = False
        self.date_sent = datetime.now()
        self.title = kwargs["title"]
        self.text = kwargs["text"]
        self.sender = kwargs["sender"]
        self.recipient = kwargs["recipient"]
        
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    title = alchemyDB.Column(alchemyDB.String(64))
    text = alchemyDB.Column(alchemyDB.String(64))
    html_body = alchemyDB.Column(alchemyDB.Text)
    date_sent = alchemyDB.Column(alchemyDB.DateTime)
    read_or_not = alchemyDB.Column(alchemyDB.Boolean)
    sender = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    recipient = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    pm_update = alchemyDB.relationship('UserUpdates', backref = 'private_message', cascade = 'all, delete-orphan')
    
    attachments = alchemyDB.relationship('PM_Attachments',
                                         backref = alchemyDB.backref('message', lazy = 'joined'),
                                         lazy = 'dynamic',
                                         cascade = 'all, delete-orphan')

    chain_children = alchemyDB.relationship('PrivateMessageReplyLink',
                                          foreign_keys = [PrivateMessageReplyLink.parentMessage],
                                          backref = alchemyDB.backref('parent_message', lazy = 'joined'),
                                          lazy = 'dynamic',
                                          cascade = 'all, delete-orphan')

    chain_parent = alchemyDB.relationship('PrivateMessageReplyLink',
                                          foreign_keys = [PrivateMessageReplyLink.childMessage],
                                          backref = alchemyDB.backref('child_message', lazy = 'joined'),
                                          lazy = 'dynamic',
                                          cascade = 'all, delete-orphan')

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        '''
            helps to sanitize blog posts.
        '''              
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_html_tags,strip=True))

alchemyDB.event.listen(PrivateMessage.text, 'set', PrivateMessage.on_changed_body)

class UserPM_Relationship(alchemyDB.Model):
    '''
        When users interact privately, they need a way to block
        one another.  This class helps keep that information.
        Also, there may be other special relationships between users and we
        store that info here.
    '''
    def __init__(self, *args, **kwargs):
        '''
            every new relationship starts
        '''
        self.main_user_id = kwargs["main_user_id"]
        self.secondary_user_id = kwargs["secondary_user_id"]
        self._relationship_type = UserRelationshipType.query.filter_by(name = 'Basic Communication').first()

        
    __tablename__ =  'user_pm_relationship'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    main_user_id = alchemyDB.Column(alchemyDB.Integer,alchemyDB.ForeignKey('users.id'))
    secondary_user_id = alchemyDB.Column(alchemyDB.Integer,alchemyDB.ForeignKey('users.id'))
    relationship_type = alchemyDB.Column(alchemyDB.Integer,alchemyDB.ForeignKey('user_relationship_type.id'))

class UserEmailConfirmationTokens(alchemyDB.Model):
    '''
        When new users register, we confirm their accounts and in particular
        their email addresses by sending an email to their address which 
        they list upon signing up. This table stores user ids and tokens
    '''
    __tablename__  = 'user_email_confirmation_tokens'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    user_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    token = alchemyDB.Column(alchemyDB.String(64))


class User(UserMixin, alchemyDB.Model):
    
    
    
    def __init__(self, **kwargs) :
        '''
            User class initialization.
        '''
        super(User,self).__init__(**kwargs)
        if self.role is None :
            if self.user_email == current_app.config['CANONWORKS_ADMIN']:
                self.role = Roles.query.filter_by(name = "Administrator").first()
            if self.role is None :
                self.role = Roles.query.filter_by(default = True).first()
    
    
    __tablename__ = 'users'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    user_email = alchemyDB.Column(alchemyDB.String(64), unique = True, index = True)
    user_name = alchemyDB.Column(alchemyDB.String(64), unique = True, index = True)
    user_pass = alchemyDB.Column(alchemyDB.String(128))
    role_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('roles.id'))
    communities = alchemyDB.Column(alchemyDB.String(64))
    articles_compared = alchemyDB.Column(alchemyDB.String(64))
    date_joined = alchemyDB.Column(alchemyDB.DateTime)
    email_confirmed = alchemyDB.Column(alchemyDB.Boolean, default = False)
    user_biography = alchemyDB.Column(alchemyDB.String(64))
    date_of_birth = alchemyDB.Column(alchemyDB.DateTime)
    users_entries = alchemyDB.relationship('Entries', backref = 'user_who_created')
    user_tags =  alchemyDB.relationship('UsersAppliedTags',
                                        foreign_keys = [UsersAppliedTags.user_id],
                                        backref = alchemyDB.backref('users_who_have_used_this_tag_for_this_article', lazy ='joined'),
                                        lazy = 'dynamic',
                                        cascade = 'all, delete-orphan')
    user_library = alchemyDB.relationship('UsersReadArticles',
                                           backref = alchemyDB.backref('users_who_have_read_this'),
                                           lazy = 'dynamic',
                                           cascade = 'all, delete-orphan')
    user_votes = alchemyDB.relationship('SourceToOutputRelationTypeVote', backref = 'user')
    users_communities = alchemyDB.relationship('UserCommunityRelation',
                                         foreign_keys = [UserCommunityRelation.user_id],
                                         backref = alchemyDB.backref('user', lazy = 'joined'),
                                         lazy = 'dynamic',
                                         cascade = 'all, delete-orphan')
    updates = alchemyDB.relationship('UserUpdates', backref = 'user', cascade = 'all, delete-orphan')
    
    sent_private_messages = alchemyDB.relationship('PrivateMessage',
                                                   foreign_keys = [PrivateMessage.sender],
                                                   backref = alchemyDB.backref('sender_user',lazy = 'joined'),
                                                   lazy = 'dynamic',
                                                   cascade = 'all, delete-orphan')
    
    received_private_messages = alchemyDB.relationship('PrivateMessage',
                                                   foreign_keys = [PrivateMessage.recipient  ],
                                                   backref = alchemyDB.backref('recipient_user',lazy = 'joined'),
                                                   lazy = 'dynamic',
                                                   cascade = 'all, delete-orphan')
    
    inbound_user_relationships = alchemyDB.relationship('UserPM_Relationship',
                                                       foreign_keys = [UserPM_Relationship.main_user_id],
                                                       backref = alchemyDB.backref('inbound_user', lazy = 'joined'),
                                                       lazy = 'dynamic',
                                                       cascade = 'all, delete-orphan')
        
    outbound_user_relationships = alchemyDB.relationship('UserPM_Relationship',
                                                       foreign_keys = [UserPM_Relationship.secondary_user_id],
                                                       backref = alchemyDB.backref('outbound_user', lazy = 'joined'),
                                                       lazy = 'dynamic',
                                                       cascade = 'all, delete-orphan')
    
    
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):    
        self.user_pass = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.user_pass, password)
    
    def __repr__(self):
        return '<User %r?'%self.user_name  
    
    def join_a_community(self, community):
        '''
            join this user to a community
        '''
        if not self.is_in_this_community(community):
            x = UserCommunityRelation(user_id = self.id, community_id = community.id)
            alchemyDB.session.add(x)

    
    def set_moderator_status(self):
        '''
            sets the status of this user to moderator.
        '''
        modID = Roles.query.filter_by(name = "Moderator").first().id
        self.role_id = modID
        alchemyDB.session.commit()
    
    def is_in_this_community(self, community):
        '''
            checks to see if this user is in the given community
        '''
        return community.users_in_this_community.filter_by(user_id = self.id).first() is not None
     
    def can(self, permissions):
        '''
            checks permissions for this user.
        '''
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions
     
     
    def is_administrator(self):
        '''
            checks to see if a user is an administrator
        '''
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        '''
            checks if this user is a moderator
        '''     
        return self.can(Permission.MODERATE_COMMENTS)
    
    
    def is_banned(self):
        '''
            checks if this user is banned
        '''
        return self.can(Permission.BANNED)
    
    def ban_user(self):
        '''
            sets a user to be banned
        '''
        self.role = Roles.query.filter_by(name = "Banned").first()
    
    def canPM_Recipient(self, recipient):
        '''
            checks if this user can private message another user.
        '''
        relationship = UserPM_Relationship.query.filter(and_(UserPM_Relationship.secondary_user_id == recipient.id, UserPM_Relationship.main_user_id == self.id)).first()
        if relationship == None or ((relationship._relationship_type.permissions & UserInteractionPermissions.SEND_PRIVATE_MESSAGES) == UserInteractionPermissions.SEND_PRIVATE_MESSAGES) :
            if relationship == None :
                newRelationship = UserPM_Relationship(main_user_id = self.id, secondary_user_id = recipient.id)
                alchemyDB.session.add(newRelationship)
                newRelationship = UserPM_Relationship(main_user_id = recipient.id, secondary_user_id = self.id)
                alchemyDB.session.add(newRelationship)
                alchemyDB.session.commit()
            return True
        return False
        
    def blockUser(self, secondaryUser):
        '''
            A user may choose to block another user.
            This will prevent any private communication between the users.
        '''
        inRel = self.inbound_user_relationships.filter_by(secondary_user_id = secondaryUser.id).first()
        outRel = secondaryUser.inbound_user_relationships.filter_by(secondary_user_id = self.id).first()        
        blockedType = UserRelationshipType.query.filter_by(name = 'Blocked').first()
        inRel._relationship_type = blockedType
        outRel._relationship_type = blockedType
        alchemyDB.session.commit()
    
    def generate_confirmation_token(self, expiration=3600):
        '''
            We want to confirm user's email addresses when they register.
            This allows us to do this by generating confirmation tokens
            which we then send in emails upon registration.
        '''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.id})
    
    def generate_email_change_token(self, emailAddress, expiration=3600):
        '''
            When a user wants to change their email, they need to
            confirm the new address.  We do this with tokens
            sent to the new email address.
        '''
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'id':self.id, 'email':emailAddress})
    
    def change_email(self, token):
        '''
            Changes a users email given the token
            sent to the new address.
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        try :
            data = s.loads(token)
        except :
            return False
        if data.get('id') != self.id:
            return False
        self.user_email = data.get('email')
        alchemyDB.session.commit()
        return True 
    
    def confirm(self, token):
        '''
            We want to confirm user's email addresses when they register.
            This allows us to do that by confirming a token that has been
            sent to a user (via email) upon registering.
        '''
        s = Serializer(current_app.config['SECRET_KEY'])
        try :
            data = s.loads(token)
        except :
            return False
        if data.get('confirm')!=self.id:
            return False
        self.email_confirmed = True
        alchemyDB.session.commit()
        return True
    
    def reset_password(self, token):
        '''
            This resets a user's password given
            the token sent to their email account.
        '''   
        pass

class Communities(alchemyDB.Model):
    '''
        As time goes on, people will develop communities and this is where we store them.
    '''
    __tablename__ = 'communities'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    community_name =  alchemyDB.Column(alchemyDB.String(64))
    date_created = alchemyDB.Column(alchemyDB.DateTime)
    users_in_this_community = alchemyDB.relationship('UserCommunityRelation',
                                                     foreign_keys = [UserCommunityRelation.community_id],
                                                     backref = alchemyDB.backref('community', lazy = 'joined'),
                                                     lazy = 'dynamic',
                                                     cascade = 'all, delete-orphan')
    srcOutRelations_in_this_community = alchemyDB.relationship('CommunityEntryToEntryRelation',
                                                               foreign_keys = [CommunityEntryToEntryRelation.community_id],
                                                               backref = alchemyDB.backref('community', lazy = 'joined'),
                                                               lazy = 'dynamic',
                                                               cascade = 'all, delete-orphan')

    comm_update = alchemyDB.relationship('UserUpdates', backref = 'community', cascade = 'all, delete-orphan')
    comm_page = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('community_page.id'))

    
class EntryCommunityRelation(alchemyDB.Model):
    '''
        an article can be associated with one or more communities
    '''
    __tablename__ = 'entry_community_rel'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    community_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('communities.id'))
    entry_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    
    

class ResponseRelationTypes(alchemyDB.Model):
    '''
        Responses are understood to be related to input articles according to
        only a set number of ways.  According to the current model, 
        these relations are understood to reflect the structure of a symmetric monoidal
        category (the one used in the work of Sardzadeh, Coecke).  
        So, an article can build on a previous article, adding new information and creating something new (monoidal product with other
        article and a morphism of the joint object).
        They can extend the original article, taking just that article and inducing new material from what is in the
        original article (morphism of original object).  A response can refute an input article (the negation of a sentence
        is discussed in the quantum linguistics literature, but is a little too complicated for me to understand at the moment).
        A response can say the same thing (which is just an isomorphism, perhaps an identity on an object).  There is also no clear relation which
        we take as a valid relation.   
    '''
    __tablename__ = 'responseRelationTypes'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    name = alchemyDB.Column(alchemyDB.String(64))
    descriptor = alchemyDB.Column(alchemyDB.String(64))
    votes_of_this_type = alchemyDB.relationship('SourceToOutputRelationTypeVote', backref = 'resp_rel_type')
    relationship_confirmations_of_this_type = alchemyDB.relationship('ConfirmedSrcOutRelType', backref = 'resp_rel_type')
       
    
    @staticmethod
    def setRelationTypesInDB(app):
        '''
            There are a few relation types that need to be set when the database is created.
        '''
        
        relationTypes = {"explains" : "explains",
                            "supports" : "supports",
                            "extends" : "extends",
                            "refutes" : "refutes",
                            "critiques" : "critiques",
                            "equivalent" : "says the same thing as",
                            "no relation" : "has no relation to"}
                            
        
        with app.app_context():
            with alchemyDB.session.no_autoflush:
                for relType in relationTypes :
                    rel = ResponseRelationTypes.query.filter_by(name = relType).first() 
                    if rel == None :
                        rel = ResponseRelationTypes(name = relType, descriptor = relationTypes[relType])
                        alchemyDB.session.add(rel)
                alchemyDB.session.commit()

    
class SourceToOutputRelationTypeVote(alchemyDB.Model):
    '''
        users vote on what the semantic value of the relationship between two articles is.
        we store those votes here
    '''
    __tablename__ =  'relationshipTypeVote'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    source_output_articles = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('sourceToOutputRel.id'))
    user_who_cast_vote = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    relationship_type = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('responseRelationTypes.id'))
    is_reversed = alchemyDB.Column(alchemyDB.Boolean)
    vote_date = alchemyDB.Column(alchemyDB.DateTime)
    successful_vote_confirmation = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('confirmedRelationshipType.id'))




class UserUpdates(alchemyDB.Model):
    '''
        when new communities are formed and when
        new articles are created, users get updates.
        Any new update is used to modify a user's banner
    '''
    __tablename__ = 'users_updates'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    user_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('users.id'))
    community_update = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('communities.id'))
    response_update = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('sourceToOutputRel.id'))
    private_message_update = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('private_message.id'))
    update_date = alchemyDB.Column(alchemyDB.DateTime)
    
    
class CommunityPage(alchemyDB.Model):
    '''
        When a community forms, it needs a home page and this is where 
        we store the information that goes into making the community hompeage.
    '''
    __tablename__ = 'community_page'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)    
    community_name = alchemyDB.Column(alchemyDB.String(64))
    banner_text =  alchemyDB.Column(alchemyDB.String(64))
    eplanation_text = alchemyDB.Column(alchemyDB.String(64))
    background_image = alchemyDB.Column(alchemyDB.String(64))
    community = alchemyDB.relationship('Communities', uselist=False, backref = 'page')
    
    
    
class ConfirmedSrcOutRelType(alchemyDB.Model):
    '''
        Once enough votes are cast and a type of relationship becomes apparent,
        we store that type here.
    '''
    __tablename__ =  'confirmedRelationshipType'
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)    
    relationship_type = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('responseRelationTypes.id'))
    is_reversed = alchemyDB.Column(alchemyDB.Boolean)
    number_of_votes = alchemyDB.Column(alchemyDB.Integer)
    date_of_confirmation = alchemyDB.Column(alchemyDB.DateTime)
    votes = alchemyDB.relationship('SourceToOutputRelationTypeVote', backref = 'vote_confirmation')
    src_out_rel_relationship = alchemyDB.relationship('SourceToOutputRelation', backref = 'confirmedRelType')    
                
class PM_Attachments(alchemyDB.Model):
    '''
        users can attach entries to their private messages.
        This is such an attachment
    '''
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    pm_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('private_message.id'))
    entry_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('entries.id'))
    community_id = alchemyDB.Column(alchemyDB.Integer, alchemyDB.ForeignKey('communities.id'))
    response_id = alchemyDB.Column(alchemyDB.Integer,alchemyDB.ForeignKey('sourceToOutputRel.id'))



class UserInteractionPermissions :
    '''
        a class containing all the permission types
    '''
    BLOCKED = 0X01
    SEND_PRIVATE_MESSAGES = 0X02

        
class UserRelationshipType(alchemyDB.Model) :
    '''
        Defines types of user interactions.
    '''   
    __tablename__ = 'user_relationship_type'     
    id = alchemyDB.Column(alchemyDB.Integer, primary_key = True)
    name = alchemyDB.Column(alchemyDB.String(64), unique = True)
    default = alchemyDB.Column(alchemyDB.Boolean, default = False, index = True)
    permissions = alchemyDB.Column(alchemyDB.Integer)
    relationshipsWithThisType = alchemyDB.relationship('UserPM_Relationship',
                                   backref='_relationship_type',
                                   lazy='joined')
    
    
    @staticmethod
    def setUserRelationshipsInDatabase(app):
        '''
            sets the basic user relationships in the database
        '''
        relationships = {
                 'Blocked' : (UserInteractionPermissions.BLOCKED, False),
                 'Basic Communication' : (UserInteractionPermissions.SEND_PRIVATE_MESSAGES, True),
                 'Moderator To User' : (UserInteractionPermissions.SEND_PRIVATE_MESSAGES, False),
                 'Admin to User' : (UserInteractionPermissions.SEND_PRIVATE_MESSAGES, False),
                 'Admin to Moderator' : (UserInteractionPermissions.SEND_PRIVATE_MESSAGES, False),
                 }
        with app.app_context():
            with alchemyDB.session.no_autoflush:
                for r in relationships :
                    rel = UserRelationshipType.query.filter_by(name = r).first()            
                    if rel == None :
                        rel = UserRelationshipType(name = r)
                    rel.permissions = relationships[r][0]
                    rel.default = relationships[r][1]
                    alchemyDB.session.add(rel)
                alchemyDB.session.commit()
    
    


    
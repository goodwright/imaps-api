import graphene
from graphene_django.types import DjangoObjectType
from graphene.relay import Connection
from .models import *

class UserType(DjangoObjectType):
    
    class Meta:
        model = User
        exclude_fields = ["password"]
    
    id = graphene.ID()
    groups = graphene.List("core.queries.GroupType")
    admin_groups = graphene.List("core.queries.GroupType")
    invitations = graphene.List("core.queries.GroupInvitationType")
    collections = graphene.List("core.queries.CollectionType")
    owned_collections = graphene.List("core.queries.CollectionType")
    all_collections = graphene.List("core.queries.CollectionType")

    def resolve_last_login(self, info, **kwargs):
        return None if "restricted" in self.__dict__ and self.restricted else self.last_login
        

    def resolve_groups(self, info, **kwargs):
        admin_groups = list(self.admin_groups.all())
        return sorted(self.groups.all(), key = lambda g: g not in admin_groups)
    

    def resolve_admin_groups(self, info, **kwargs):
        if "restricted" in self.__dict__ and self.restricted: return None
        return self.admin_groups.all()
    

    def resolve_invitations(self, info, **kwargs):
        if "restricted" in self.__dict__ and self.restricted: return None
        return self.group_invitations.all()
    

    def resolve_collections(self, info, **kwargs):
        if "restricted" in self.__dict__ and self.restricted:
            return self.collections.filter(private=False)
        return self.collections.all()
    

    def resolve_owned_collections(self, info, **kwargs):
        if "restricted" in self.__dict__ and self.restricted:
            return self.owned_collections.filter(private=False)
        return self.owned_collections.all()
    

    def resolve_all_collections(self, info, **kwargs):
        if "restricted" in self.__dict__ and self.restricted:
            return list(self.owned_collections.filter(private=False)) + \
                list(self.collections.filter(private=False))
        return list(self.owned_collections.all()) + list(self.collections.all())



class GroupType(DjangoObjectType):
    
    class Meta:
        model = Group
    
    id = graphene.ID()
    user_count = graphene.Int()
    users = graphene.List("core.queries.UserType")
    admins = graphene.List("core.queries.UserType")
    invitations = graphene.List("core.queries.GroupInvitationType")

    def resolve_user_count(self, info, **kwargs):
        return self.users.count()
        

    def resolve_users(self, info, **kwargs):
        return self.users.all()
    

    def resolve_admins(self, info, **kwargs):
        return self.admins.all()
    

    def resolve_invitations(self, info, **kwargs):
        return self.group_invitations.all()




class GroupInvitationType(DjangoObjectType):
    
    class Meta:
        model = GroupInvitation
    
    id = graphene.ID()



class CollectionType(DjangoObjectType):
    
    class Meta:
        model = Collection
    
    id = graphene.ID()
    papers = graphene.List("core.queries.PaperType")

    def resolve_papers(self, info, **kwargs):
        return self.papers.all()



class CollectionConnection(Connection):

    class Meta:
        node = CollectionType



class PaperType(DjangoObjectType):
    
    class Meta:
        model = Paper
    
    id = graphene.ID()
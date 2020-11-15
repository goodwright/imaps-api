import time
import json
import graphene
from graphql import GraphQLError
from django.contrib.auth.hashers import check_password
from core.models import User
from core.forms import *
from core.arguments import create_mutation_arguments

class SignupMutation(graphene.Mutation):

    Arguments = create_mutation_arguments(SignupForm)

    access_token = graphene.String()

    def mutate(self, info, **kwargs):
        form = SignupForm(kwargs)
        if form.is_valid():
            form.instance.last_login = time.time()
            form.save()
            info.context.refresh_token = form.instance.make_refresh_jwt()
            return SignupMutation(access_token=form.instance.make_access_jwt())
        raise GraphQLError(json.dumps(form.errors))



class LoginMutation(graphene.Mutation):

    class Arguments:
        username = graphene.String()
        password = graphene.String()
    
    access_token = graphene.String()

    def mutate(self, info, **kwargs):
        user = User.objects.filter(username=kwargs["username"]).first()
        if user:
            if check_password(kwargs["password"], user.password):
                info.context.refresh_token = user.make_refresh_jwt()
                user.last_login = time.time()
                user.save()
                return LoginMutation(access_token=user.make_access_jwt())
        raise GraphQLError(json.dumps({"username": "Invalid credentials"}))



class RefreshMutation(graphene.Mutation):

    access_token = graphene.String()

    def mutate(self, info, **kwargs):
        token = info.context.COOKIES.get("refresh_token")
        if not token:
            raise GraphQLError(json.dumps({"token": "No refresh token supplied"}))
        user = User.from_token(token)
        if user:
            info.context.refresh_token = user.make_refresh_jwt()
            return RefreshMutation(access_token=user.make_access_jwt())
        raise GraphQLError(json.dumps({"token": "Refresh token not valid"}))
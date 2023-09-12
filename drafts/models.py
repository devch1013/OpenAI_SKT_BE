from django.db import models
from users.models import User

# Create your models here.


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    suggestion_flag = models.BooleanField(default=False)
    selected_suggestion = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    project_name = models.CharField(max_length=200)
    purpose = models.TextField(blank=True, null=True)
    table = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)


class DataSourceSuggestion(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    source = models.CharField(max_length=20, null=True, blank=True)
    data_type = models.CharField(max_length=20, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    # icon = models.CharField(max_length=300, null=True, blank=True)
    link = models.TextField(null=True, blank=True)


class DataSource(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    data_type = models.CharField(max_length=10)
    data = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class Draft(models.Model):
    status = models.IntegerField(null=True, default=0)
    draft = models.TextField()
    table = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)


class AiDraftModification(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    query_text = models.TextField(null=True, blank=True)
    ai_request = models.TextField(null=True, blank=True)
    result_text = models.TextField(null=True, blank=True)




class Conversation(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    length = models.IntegerField(default=0)
    stage_history = models.CharField(max_length=200, default="")


class Utterance(models.Model):
    id = models.AutoField(primary_key=True)
    user_side = models.TextField(blank=True, null=True, default="")
    ai_side = models.TextField(blank=True, null=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)
    time_to_response = models.IntegerField(default=0)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    # text = models.TextField(max_length=500)  ## 발화내용
    stage = models.IntegerField(blank=True, null=True)
from django.contrib.auth.models import User, Group

user = User.objects.create_user('admin', password='KepalaRuangan')
user.is_staff = True
user.save()

group, _ = Group.objects.get_or_create(name='Kepala Ruangan')
user.groups.add(group)

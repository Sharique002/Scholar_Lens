from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0007_paperauthor_match_score_paperauthor_match_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importrun',
            name='source',
            field=models.CharField(
                choices=[('ORCID', 'ORCID'), ('CROSSREF', 'Crossref'), ('SCOPUS', 'Scopus')],
                max_length=50,
            ),
        ),
    ]

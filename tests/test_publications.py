"""Tests for M2 Publication fields, trigram index, soft merge, and title normalisation."""
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramSimilarity

from papers.models import ResearchPaper
from papers.text import normalise_title


class TitleNormalisationTests(TestCase):
    def test_accents_stripped(self):
        self.assertEqual(normalise_title("Modèles d'Apprentissage"), "modeles d apprentissage")
        self.assertEqual(normalise_title("Naïve Schrödinger"), "naive schrodinger")

    def test_ampersand_to_and(self):
        self.assertEqual(normalise_title("Deep Learning & Robotics"), "deep learning and robotics")

    def test_html_stripped(self):
        self.assertEqual(normalise_title("<i>Graph</i> <b>Neural</b> Networks"), "graph neural networks")

    def test_whitespace_and_punctuation(self):
        self.assertEqual(normalise_title("  Multi-Agent    Systems: A Survey!  "), "multi agent systems a survey")


class PublicationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('author1', password='password123')

    def test_fields_and_auto_normalisation(self):
        paper = ResearchPaper.objects.create(
            title="A Survey on Graph Neural Networks & Applications",
            abstract="Survey abstract",
            uploader=self.user,
            publication_date=date(2023, 6, 15),
            venue="IEEE Transactions on Pattern Analysis",
            pub_type="JOURNAL",
            doi="10.1109/TPAMI.2023.1234567"
        )

        self.assertEqual(paper.venue, "IEEE Transactions on Pattern Analysis")
        self.assertEqual(paper.pub_type, "JOURNAL")
        self.assertEqual(paper.doi, "10.1109/TPAMI.2023.1234567")
        self.assertEqual(paper.year, 2023)
        self.assertEqual(paper.normalised_title, "a survey on graph neural networks and applications")

    def test_soft_merge_and_resolve(self):
        canonical = ResearchPaper.objects.create(
            title="Canonical Paper on Diffusion Models",
            abstract="Canonical abstract",
            uploader=self.user,
            year=2024
        )
        intermediate = ResearchPaper.objects.create(
            title="Intermediate Duplicate Paper",
            abstract="Intermediate abstract",
            uploader=self.user,
            year=2024,
            merged_into=canonical
        )
        old_duplicate = ResearchPaper.objects.create(
            title="Old Duplicate Paper",
            abstract="Old duplicate abstract",
            uploader=self.user,
            year=2024,
            merged_into=intermediate
        )

        # Active manager excludes merged papers
        active_ids = list(ResearchPaper.objects.values_list('id', flat=True))
        self.assertIn(canonical.id, active_ids)
        self.assertNotIn(intermediate.id, active_ids)
        self.assertNotIn(old_duplicate.id, active_ids)

        # all_objects includes all papers
        all_ids = list(ResearchPaper.all_objects.values_list('id', flat=True))
        self.assertIn(canonical.id, all_ids)
        self.assertIn(intermediate.id, all_ids)
        self.assertIn(old_duplicate.id, all_ids)

        # resolve() follows merged_into chain
        self.assertEqual(canonical.resolve().id, canonical.id)
        self.assertEqual(intermediate.resolve().id, canonical.id)
        self.assertEqual(old_duplicate.resolve().id, canonical.id)

    def test_trigram_similarity_query(self):
        ResearchPaper.objects.create(
            title="Convolutional Neural Networks for Biomedical Image Segmentation",
            abstract="U-Net architecture",
            uploader=self.user,
            year=2021
        )
        norm_query = normalise_title("Convolutional Neural Network for Biomedical Image Segmentation")

        matches = (
            ResearchPaper.objects.annotate(similarity=TrigramSimilarity('normalised_title', norm_query))
            .filter(similarity__gt=0.7)
            .order_by('-similarity')
        )
        self.assertEqual(matches.count(), 1)

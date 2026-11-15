from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'order', 'author',
            'target', 'rating', 'text',
            'author_name', 'created_at',
        ]

        read_only_fields = ['id', 'author', 'author_name', 'target', 'created_at']

    def get_author_name(self, obj):
        if obj.author is None:
            return "Mijoz"
        return obj.author.first_name or obj.author.get_full_name() or "Mijoz"

    def validate_text(self, value):
        return (value or '').strip()

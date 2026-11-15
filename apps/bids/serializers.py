from rest_framework import serializers
from .models import Bid



class BidSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bid
        fields = ['id', 'order', 'master', 'price', 'duration_days', 'comments', 'status', 'created_at']
        read_only_fields = ['id', 'master', 'status', 'created_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return value

    def validate_duration_days(self, value):
        if value < 1:
            raise serializers.ValidationError("Muddat kamida 1 kun bo'lishi kerak.")
        return value



class BidUpdateSerializer(BidSerializer):

    class Meta(BidSerializer.Meta):
        read_only_fields = ['id', 'order', 'master', 'status', 'created_at']



class BidWithMasterSerializer(BidSerializer):

    master_name = serializers.SerializerMethodField()
    master_rating = serializers.DecimalField(source='master.rating_avg', max_digits=2, decimal_places=1, read_only=True)
    master_jobs_done = serializers.IntegerField(source='master.jobs_done', read_only=True)

    class Meta(BidSerializer.Meta):
        fields = BidSerializer.Meta.fields + ['master_name', 'master_rating', 'master_jobs_done']
        read_only_fields = fields

    def get_master_name(self, obj):
        user = obj.master.user
        return user.get_full_name() or user.username
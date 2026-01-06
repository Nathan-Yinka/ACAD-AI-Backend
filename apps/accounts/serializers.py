"""
Serializers for the accounts app.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    username = serializers.CharField(
        max_length=150,
        min_length=1,
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            'required': 'Username is required.',
            'blank': 'Username cannot be blank.',
            'max_length': 'Username cannot exceed 150 characters.',
            'min_length': 'Username must be at least 1 character.',
        }
    )
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Email is required.',
            'blank': 'Email cannot be blank.',
            'invalid': 'Enter a valid email address.',
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        validators=[validate_password],
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be blank.',
        }
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Password confirmation is required.',
            'blank': 'Password confirmation cannot be blank.',
        }
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }

    def validate_username(self, value):
        """Validate username is not empty and has proper length."""
        if not value or not value.strip():
            raise serializers.ValidationError('Username cannot be empty or whitespace only.')
        if len(value.strip()) < 1:
            raise serializers.ValidationError('Username must be at least 1 character.')
        if len(value) > 150:
            raise serializers.ValidationError('Username cannot exceed 150 characters.')
        
        if User.objects.filter(username=value.strip()).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        
        return value.strip()

    def validate_email(self, value):
        """Validate email is not empty and is valid format."""
        if not value or not value.strip():
            raise serializers.ValidationError('Email cannot be empty or whitespace only.')
        
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        
        return email

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Password fields did not match.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Always set is_student to True for new registrations
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_student=True
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Email is required.',
            'blank': 'Email cannot be blank.',
            'invalid': 'Enter a valid email address.',
        }
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        allow_blank=False,
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be blank.',
        }
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                              username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    """
    username = serializers.CharField(
        max_length=150,
        min_length=1,
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            'required': 'Username is required.',
            'blank': 'Username cannot be blank.',
            'max_length': 'Username cannot exceed 150 characters.',
            'min_length': 'Username must be at least 1 character.',
        }
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=False,
        error_messages={
            'required': 'Email is required.',
            'blank': 'Email cannot be blank.',
            'invalid': 'Enter a valid email address.',
        }
    )
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_student', 'created_at')
        read_only_fields = ('id', 'created_at', 'is_student')
    
    def validate_username(self, value):
        """Validate username is not empty and has proper length."""
        if not value or not value.strip():
            raise serializers.ValidationError('Username cannot be empty or whitespace only.')
        if len(value.strip()) < 1:
            raise serializers.ValidationError('Username must be at least 1 character.')
        if len(value) > 150:
            raise serializers.ValidationError('Username cannot exceed 150 characters.')
        return value.strip()
    
    def validate_email(self, value):
        """Validate email is not empty and is valid format."""
        if not value or not value.strip():
            raise serializers.ValidationError('Email cannot be empty or whitespace only.')
        return value.strip().lower()


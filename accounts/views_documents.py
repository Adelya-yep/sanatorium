# accounts/views_documents.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from .forms_documents import DocumentUploadForm
from .models import GuestProfile, EncryptedDocument
from django.contrib.auth.models import User


@login_required
def upload_documents(request):
    """Упрощенная страница загрузки документов"""
    profile, created = GuestProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST)
        if form.is_valid():
            try:
                document_type = form.cleaned_data['document_type']

                # Создаем запись документа
                document = EncryptedDocument.objects.create(
                    profile=profile,
                    document_type=document_type,
                    uploaded_by=request.user
                )

                # Обновляем статус профиля
                profile.document_status = 'pending'
                profile.save()

                messages.success(request, f'Документ "{document.get_document_type_display()}" загружен на проверку!')
                return redirect('profile')

            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
    else:
        form = DocumentUploadForm()

    # Получаем существующие документы
    documents = profile.documents.all()

    return render(request, 'documents/upload.html', {
        'form': form,
        'profile': profile,
        'documents': documents,
    })


@login_required
@permission_required('accounts.can_verify_documents', raise_exception=True)
def verify_documents(request, user_id):
    """Упрощенная админская страница проверки документов"""
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(GuestProfile, user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        document_id = request.POST.get('document_id')

        try:
            document = EncryptedDocument.objects.get(id=document_id, profile=profile)

            if action == 'verify':
                document.verified = True
                document.verified_at = timezone.now()
                document.verified_by = request.user
                document.save()

                # Обновляем статус профиля
                profile.document_status = 'verified'
                profile.document_verified_at = timezone.now()
                profile.document_verified_by = request.user
                profile.save()

                messages.success(request, '✅ Документ проверен!')

            elif action == 'reject':
                profile.document_status = 'rejected'
                profile.save()
                messages.warning(request, '❌ Документ отклонен')

        except EncryptedDocument.DoesNotExist:
            messages.error(request, 'Документ не найден')

    # Получаем все документы пользователя
    documents = profile.documents.all()

    return render(request, 'admin/verify_documents.html', {
        'profile_user': user,
        'profile': profile,
        'documents': documents,
    })
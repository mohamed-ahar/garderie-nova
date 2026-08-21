from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Lesson
from .forms import LessonForm # Ghadi n-gaduha f forms.py

# --- 1. Dashboard / List View ---
class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    template_name = 'lesson_list.html'
    context_object_name = 'lessons'

    def get_queryset(self):
        user = self.request.user
        # Ila kan Director awla Owner, i-chouf kolchi
        if user.role_type in ['director', 'owner']:
            return Lesson.objects.all()
        # Ila kan Educator, i-chouf ghir dorouss dyalo
        elif user.role_type == 'educator':
            return Lesson.objects.filter(educator__user=user)
        return Lesson.objects.none()

# --- 2. Create Lesson (Ghir l-Director/Owner) ---
class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'lesson_form.html'
    success_url = reverse_lazy('curriculum:lesson_list')

    def test_func(self):
        # Kay-checki wach l-user 3ndo l-haq i-creayi
        return self.request.user.role_type in ['director', 'owner']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

# --- 3. Update Lesson ---
class LessonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'lesson_form.html'
    success_url = reverse_lazy('curriculum:lesson_list')

    def test_func(self):
        return self.request.user.role_type in ['director', 'owner']

# --- 4. Delete Lesson ---
class LessonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lesson
    template_name = 'lesson_confirm_delete.html'
    success_url = reverse_lazy('curriculum:lesson_list')

    def test_func(self):
        return self.request.user.role_type in ['director', 'owner']

# --- 5. Lesson Detail (Fin kiban l-PDF o Video) ---
class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'lesson_detail.html'
    context_object_name = 'lesson'

# --- 6. API dial Badge (li khdemna bih f Sidebar) ---
#hadi mnbe3d

def lesson_count_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    user = request.user
    if user.role_type == 'educator':
        count = Lesson.objects.filter(educator__user=user).count()
    else:
        count = Lesson.objects.count()
        
    return JsonResponse({'count': count})

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import Lesson
from .forms import LessonForm 
from django.db.models import Q

# --- 1. Dashboard / List View ---
class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    # template_name = 'lesson_list.html'
    context_object_name = 'lessons'

    def get_queryset(self):
        user = self.request.user
        
        # Optimization: select_related l-'created_by' hit hia li fiha l-Director
        base_qs = Lesson.objects.all().select_related('created_by', 'educator__user').order_by('-created_at')

        # 1. Ila kan Director: i-chouf dorouss li 'Created By' houwa
        if user.role_type == 'director':
            return base_qs.filter(created_by=user)
        
        # 2. Ila kan Educator: i-chouf dorouss li 'Assigned' lih f l-field 'educator'
        elif user.role_type == 'educator':
            return base_qs.filter(educator__user=user)

        return Lesson.objects.none()
# --- 2. Create Lesson (Ghir l-Director/Owner) ---
class LessonCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'lesson_form.html'
    # success_url = reverse_lazy('curriculum:lesson_list')

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
    # success_url = reverse_lazy('curriculum:lesson_list')

    def test_func(self):
        return self.request.user.role_type in ['director', 'owner']

# --- 4. Delete Lesson ---
class LessonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lesson
    template_name = 'lesson_confirm_delete.html'
    # success_url = reverse_lazy('curriculum:lesson_list')

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
    # 1. Kant-choufou imta akher marra dkhl l-user l-safha dial l-lessons
    # Khass t-zid had l-field 'last_lesson_view' f Profile dyalk awla n-sta3mlo last_login ghi bach n-jerbo
    last_viewed = getattr(user, 'last_lesson_view', user.last_login)

    # 2. Kan-filteriw ghir l-lessons li t-creaw men l-marra l-khera li dkhl fiha
    base_query = Lesson.objects.filter(created_at__gt=last_viewed)

    if user.role_type == 'educator':
        count = base_query.filter(educator__user=user).count()
    elif user.role_type in ['owner', 'director', 'vice_director']:
        # Hna tqder t-zid l-filter dial l-organization/center li drna f l-form qbila
        count = base_query.count()
    else:
        count = 0
        
    return JsonResponse({'count': count})

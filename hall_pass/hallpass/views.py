# views.py
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from .models import Student, PassRecord, Ban, HallwayCapacity, TenantUser
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render
from django.db.models import Count
import qrcode
from qrcode.image.pil import PilImage
from io import BytesIO
from django.utils.safestring import mark_safe
import base64
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from .forms import TenantUserForm

#Check in and out system
@login_required
def checkout(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # Logic to check if the student can be checked out
    open_check = PassRecord.objects.filter(student=student, open=True)
    context = {}  # Initialize an empty context dictionary
    if open_check.exists():
        # Check In Student
        open_check.update(open=False, in_or_out='In')
        context['alert'] = 'success'
        context['message'] = 'Student had an open pass and has been checked in.'
    else:
        # Check for bans involving this student
        bans_involving_student = Ban.objects.filter(Q(first_student=student) | Q(second_student=student))
        ban_exists = False
        capacity_met = False
        for ban in bans_involving_student:
            other_student = ban.second_student if ban.first_student == student else ban.first_student
            if PassRecord.objects.filter(student=other_student, open=True).exists():
                PassRecord.objects.create(
                    student=student,
                    approved=False,
                    details=f"Could not check out. {other_student} has an open hall pass.",
                    in_or_out='In',
                    open=False,
                    teacher=request.user
                )
                context['alert'] = 'danger'
                context['message'] = 'Cannot check out student, associated student has an open pass due to a ban.'
                ban_exists = True
                break  # Exit the loop as we have found a ban
        #Check to ensure that gender capacity has not been met.
        capacity_value = get_object_or_404(HallwayCapacity, gender=student.gender).limit
        print(capacity_value)
        students_in_hallway = PassRecord.objects.filter(open=True, student__gender=student.gender).count()
        print (students_in_hallway)
        if students_in_hallway >= capacity_value:
            PassRecord.objects.create(
                student=student,
                approved=False,
                details=f"Could not check out. Too many students in the hallway.",
                in_or_out='In',
                open=False,
                teacher=request.user
            )
            context['alert'] = 'danger'
            context['message'] = 'Cannot check out student, too many students in the hallway.'
            capacity_met = True

        if not ban_exists and not capacity_met:
            # If the student is neither checked out nor banned with another student who is checked out, proceed to check them out
            PassRecord.objects.create(
                student=student,
                approved=True,
                details="Checked out automatically via URL",
                in_or_out='Out',
                open=True,
                teacher=request.user
            )
            context['alert'] = 'success'
            context['message'] = 'Student checked out successfully.'

    # Render the checkout template with the context
    return render(request, 'checkout_status.html', context)

#View which students are in the hallways
@login_required
def students_out(request):
    open_passes = PassRecord.objects.filter(open=True)
    students_with_timeouts = [{
        'student': open_pass.student,
        'time_out': open_pass.date
    } for open_pass in open_passes]
    return render(request, 'students_out.html', {'students_with_timeouts': students_with_timeouts})
#Populates a table showing ALL students and how many hall passes they've used.
@login_required
def student_passes_count(request):
    # This will create a QuerySet of students with an extra 'passes_count' attribute
    # that represents the number of PassRecord instances associated with each student.
    students_with_passes = Student.objects.annotate(passes_count=Count('passrecord'))

    return render(request, 'student_passes_count.html', {'students_with_passes': students_with_passes})

@login_required
def view_passes(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    passes = PassRecord.objects.filter(student=student)
    context = {'passes': passes, 'student': student}
    return render(request, 'individual_passes.html', context)

@login_required
@login_required
def individual_pass(request, student_id):
    context = {}
    student = get_object_or_404(Student, id=student_id)
    tenant = request.tenant

    # QR code generation
    img = qrcode.make(
        f'http://{tenant.domain_url}:8000/checkout/{student.id}',
        image_factory=PilImage,
        box_size=10
    )

    # Save to BytesIO
    stream = BytesIO()
    img.save(stream)
    stream.seek(0)

    # Encode the image to base64
    img_base64 = base64.b64encode(stream.getvalue()).decode('utf-8')
    context['img_base64'] = mark_safe(img_base64)
    context['name'] = student

    return render(request, "view_pass.html", context=context)

@login_required
def all_student_passes(request):
    students = Student.objects.all()
    hall_passes = []
    tenant = request.tenant

    for student in students:
        # Generate QR code for each student
        img = qrcode.make(
            f'http://{tenant.domain_url}:8000/checkout/{student.id}',
            image_factory=PilImage,
            box_size=10
        )

        # Save to BytesIO
        stream = BytesIO()
        img.save(stream)
        stream.seek(0)

        # Encode the image to base64
        img_base64 = base64.b64encode(stream.getvalue()).decode('utf-8')

        # Append student and their QR code to the hall_passes list
        hall_passes.append({
            'name': student,
            'student_id': student.id,
            'img_base64': mark_safe(img_base64)
        })

    return render(request, "all_student_passes.html", {'hall_passes': hall_passes})

class CustomLoginView(LoginView):
    template_name = 'login.html'
    # You can add more customization here if needed

@login_required
def view_profile(request):
    teacher_passes = PassRecord.objects.filter(teacher=request.user)
    total_passes = teacher_passes.count()
    return render(request, 'profile.html', {'user': request.user, 'passes': teacher_passes, 'count': total_passes})

@login_required
def passes_by_teacher(request, teacher_id):
    students = Student.objects.filter(homeroom_teacher=teacher_id)
    hall_passes = []
    tenant = request.tenant

    for student in students:
        # Generate QR code for each student
        img = qrcode.make(
            f'http://{tenant.domain_url}:8000/checkout/{student.id}',
            image_factory=PilImage,
            box_size=10
        )

        # Save to BytesIO
        stream = BytesIO()
        img.save(stream)
        stream.seek(0)

        # Encode the image to base64
        img_base64 = base64.b64encode(stream.getvalue()).decode('utf-8')

        # Append student and their QR code to the hall_passes list
        hall_passes.append({
            'name': student,
            'student_id': student.id,
            'img_base64': mark_safe(img_base64)
        })

    return render(request, "all_student_passes.html", {'hall_passes': hall_passes})
@login_required
def list_teachers(request):
    teachers = TenantUser.objects.all()

    return render(request, "teacher_list.html", {'teachers': teachers})



@login_required
def create_tenant_user(request):
    if request.method == 'POST':
        form = TenantUserForm(request.POST)
        if form.is_valid():
            # Save the form data to create a new TenantUser instance
            tenant_user = form.save()
            # Redirect to a success page or do other actions
            return redirect('success_page_name')  # Replace 'success_page_name' with the actual URL name
    else:
        form = TenantUserForm()

    return render(request, 'create_tenant_user.html', {'form': form})

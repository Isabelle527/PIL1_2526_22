from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from comptes.models import Profile
from .forms import ContactForm, MessageForm, SlotSuggestionForm, GoalProposalForm, InitiationMiniForm
from .models import Conversation, ContactMessage, Message

AVATAR_COLORS = ['#6366f1','#f59e0b','#ec4899','#14b8a6','#8b5cf6','#ef4444','#10b981','#3b82f6']


def home(request):
    return render(request, 'index.html')


def fonctionnalites(request):
    return render(request, 'fonctionnalites.html')


def mentors(request):
    query = request.GET.get('q', '')
    filiere = request.GET.get('filiere', '')
    role = request.GET.get('role', 'mentor')
    availability = request.GET.get('availability', '')
    error_message = None
    mentors = []
    current_profile = None
    try:
        mentors_qs = Profile.objects.filter(role__in=['mentor', 'both']).order_by('-created_at')
        if filiere:
            mentors_qs = mentors_qs.filter(filiere__icontains=filiere)
        if query:
            mentors_qs = mentors_qs.filter(
                Q(user__username__icontains=query) |
                Q(competences__icontains=query) |
                Q(bio__icontains=query)
            )
        mentors = list(mentors_qs)
        if request.user.is_authenticated:
            current_profile = getattr(request.user, 'profile', None)
        if current_profile:
            for mentor in mentors:
                mentor.match_score = current_profile.compatibility_score_with(mentor)
            mentors.sort(key=lambda p: p.match_score, reverse=True)
    except Exception as e:
        error_message = 'Erreur opérationnelle. Migrations non appliquées.'
        mentors = []
    return render(request, 'mentors.html', {
        'mentors': mentors, 'query': query, 'filiere': filiere,
        'current_profile': current_profile, 'role': role,
        'availability': availability, 'error_message': error_message,
    })


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        contact_message = form.save(commit=False)
        if request.user.is_authenticated:
            contact_message.user = request.user
        contact_message.save()
        request.session['contact_sent'] = True
        return redirect('contact')
    contact_sent = request.session.pop('contact_sent', False)
    return render(request, 'contact.html', {'form': form, 'contact_sent': contact_sent})


def ressources(request):
    return render(request, 'ressources.html')


@login_required
def conversations(request):
    convs = request.user.conversations.order_by('-updated_at')
    conversation_list = []
    for i, conv in enumerate(convs):
        other = conv.participants.exclude(pk=request.user.pk).first() or request.user
        latest_message = conv.messages.order_by('-timestamp').first()
        conversation_list.append({
            'conversation': conv,
            'other': other,
            'latest_message': latest_message,
            'color': AVATAR_COLORS[i % len(AVATAR_COLORS)],
        })
    return render(request, 'conversations.html', {'conversations': conversation_list})


@login_required
def messagerie(request):
    """Vue messagerie avec liste conversations + chat actif"""
    convs = request.user.conversations.order_by('-updated_at')
    conversation_list = []
    for i, conv in enumerate(convs):
        other = conv.participants.exclude(pk=request.user.pk).first() or request.user
        latest_message = conv.messages.order_by('-timestamp').first()
        conversation_list.append({
            'conversation': conv,
            'other': other,
            'latest_message': latest_message,
            'color': AVATAR_COLORS[i % len(AVATAR_COLORS)],
        })

    # Conversation active (optionnel via ?conv=id)
    active_conv_id = request.GET.get('conv')
    active_conv = None
    conv_messages = []
    other_participant = None
    if active_conv_id:
        try:
            active_conv = Conversation.objects.get(pk=active_conv_id)
            if request.user in active_conv.participants.all():
                conv_messages = active_conv.messages.order_by('timestamp')
                other_participant = active_conv.participants.exclude(pk=request.user.pk).first()
        except Conversation.DoesNotExist:
            pass

    return render(request, 'messagerie.html', {
        'conversations': conversation_list,
        'active_conv': active_conv,
        'messages': conv_messages,
        'other_participant': other_participant,
    })


@login_required
def send_in_messagerie(request, conversation_id):
    """Gère les POST depuis messagerie.html et redirige vers messagerie?conv=ID"""
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('messagerie')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_message':
            body = request.POST.get('body', '').strip()
            if body:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    type='text',
                    body=body
                )
                conversation.save()
        elif action == 'suggest_slots':
            slots_text = request.POST.get('slots', '').strip()
            if slots_text:
                Message.objects.create(conversation=conversation, sender=request.user, type='slot_suggestion', body=slots_text)
                conversation.suggested_slots = {'raw': slots_text}
                conversation.save()
        elif action == 'propose_goal':
            goal_text = request.POST.get('goal', '').strip()
            if goal_text:
                Message.objects.create(conversation=conversation, sender=request.user, type='goal_proposal', body=goal_text)
                conversation.initial_goal = goal_text
                conversation.save()

    return redirect(f'/messagerie/?conv={conversation_id}')



    other = get_object_or_404(User, pk=user_id)
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other)
    return redirect(f'/messagerie/?conv={conversation.id}')


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('conversations')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_message':
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.conversation = conversation
                message.sender = request.user
                message.type = 'text'
                message.save()
                conversation.save()
                return redirect('conversation_detail', conversation_id=conversation.id)
        elif action == 'suggest_slots':
            slot_form = SlotSuggestionForm(request.POST)
            if slot_form.is_valid():
                slots_text = slot_form.cleaned_data['slots']
                Message.objects.create(conversation=conversation, sender=request.user, type='slot_suggestion', body=slots_text)
                conversation.suggested_slots = {'raw': slots_text}
                conversation.save()
                return redirect('conversation_detail', conversation_id=conversation.id)
        elif action == 'propose_goal':
            goal_form = GoalProposalForm(request.POST)
            if goal_form.is_valid():
                goal_text = goal_form.cleaned_data['goal']
                Message.objects.create(conversation=conversation, sender=request.user, type='goal_proposal', body=goal_text)
                conversation.initial_goal = goal_text
                conversation.save()
                return redirect('conversation_detail', conversation_id=conversation.id)
        elif action == 'initiation_form':
            init_form = InitiationMiniForm(request.POST)
            if init_form.is_valid():
                expectations = init_form.cleaned_data.get('expectations')
                Message.objects.create(conversation=conversation, sender=request.user, type='form_submission', body=expectations or '')
                conversation.initiation_form = expectations or ''
                conversation.save()
                return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
        slot_form = SlotSuggestionForm()
        goal_form = GoalProposalForm()
        init_form = InitiationMiniForm()

    messages = conversation.messages.order_by('timestamp')
    other_participant = conversation.participants.exclude(pk=request.user.pk).first()
    return render(request, 'conversation.html', {
        'conversation': conversation,
        'messages': messages,
        'form': form,
        'slot_form': slot_form,
        'goal_form': goal_form,
        'init_form': init_form,
        'other_participant': other_participant,
    })


@login_required
def start_chat(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other)
    return redirect(f'/messagerie/?conv={conversation.id}')

import datetime
from io import BytesIO
from django.http import JsonResponse, HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.shortcuts import render, get_object_or_404
from attendance.decorators import group_login_required, staff_required
from attendance.models import CareGroup, Member, MeetingDate, AttendanceRecord, Visitor


def _default_date_range():
    today = datetime.date.today()
    return today - datetime.timedelta(days=91), today


def _parse_date_params(request):
    try:
        from_date = datetime.date.fromisoformat(request.GET.get('from', ''))
    except ValueError:
        from_date = None
    try:
        to_date = datetime.date.fromisoformat(request.GET.get('to', ''))
    except ValueError:
        to_date = None
    if not from_date or not to_date:
        from_date, to_date = _default_date_range()
    return from_date, to_date


@group_login_required
def analytics(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    return render(request, 'attendance/analytics.html', {'group': group})


@group_login_required
def analytics_data(request):
    group = get_object_or_404(CareGroup, pk=request.session['group_id'])
    from_date, to_date = _parse_date_params(request)

    meetings = MeetingDate.objects.filter(
        group=group, date__gte=from_date, date__lte=to_date
    ).order_by('date')
    meeting_ids = list(meetings.values_list('pk', flat=True))
    meeting_count = len(meeting_ids)

    weekly_labels, weekly_totals = [], []
    for meeting in meetings:
        present = AttendanceRecord.objects.filter(
            meeting_date=meeting, is_present=True
        ).count()
        visitors = Visitor.objects.filter(meeting_date=meeting).count()
        weekly_labels.append(str(meeting.date))
        weekly_totals.append(present + visitors)

    active_members = Member.objects.filter(group=group, is_active=True)
    member_rates = []
    for member in active_members:
        attended = AttendanceRecord.objects.filter(
            meeting_date_id__in=meeting_ids, member=member, is_present=True
        ).count()
        rate = round((attended / meeting_count) * 100, 1) if meeting_count > 0 else 0.0
        member_rates.append({
            'name': member.name,
            'rate': rate,
            'attended': attended,
            'total': meeting_count,
        })

    return JsonResponse({
        'weekly': {'labels': weekly_labels, 'totals': weekly_totals},
        'member_rates': member_rates,
        'from_date': str(from_date),
        'to_date': str(to_date),
    })


@staff_required
def admin_dashboard(request):
    groups = CareGroup.objects.all().order_by('name')
    return render(request, 'attendance/admin_dashboard.html', {'groups': groups})


@staff_required
def admin_dashboard_data(request):
    from_date, to_date = _parse_date_params(request)
    groups = CareGroup.objects.all().order_by('name')
    result = []

    for group in groups:
        meetings = MeetingDate.objects.filter(
            group=group, date__gte=from_date, date__lte=to_date
        ).order_by('date')
        meeting_ids = list(meetings.values_list('pk', flat=True))
        meeting_count = len(meeting_ids)

        weekly_labels, weekly_totals = [], []
        for meeting in meetings:
            present = AttendanceRecord.objects.filter(
                meeting_date=meeting, is_present=True
            ).count()
            visitors = Visitor.objects.filter(meeting_date=meeting).count()
            weekly_labels.append(str(meeting.date))
            weekly_totals.append(present + visitors)

        active_member_count = Member.objects.filter(group=group, is_active=True).count()
        total_attended = AttendanceRecord.objects.filter(
            meeting_date_id__in=meeting_ids, is_present=True
        ).count()
        denominator = meeting_count * active_member_count
        overall_rate = round((total_attended / denominator) * 100, 1) if denominator > 0 else 0.0

        result.append({
            'name': group.name,
            'weekly': {'labels': weekly_labels, 'totals': weekly_totals},
            'overall_rate': overall_rate,
            'meeting_count': meeting_count,
        })

    return JsonResponse({
        'groups': result,
        'from_date': str(from_date),
        'to_date': str(to_date),
    })


@staff_required
def export_csv(request):
    wb = Workbook()
    wb.remove(wb.active)  # remove default empty sheet

    # Styles
    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_fill = PatternFill('solid', fgColor='007AFF')
    date_font = Font(bold=True, size=10)
    date_fill = PatternFill('solid', fgColor='F2F2F7')
    center = Alignment(horizontal='center', vertical='center')
    thin = Side(style='thin', color='DDDDDD')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    groups = CareGroup.objects.all().order_by('name')

    for group in groups:
        ws = wb.create_sheet(title=group.name[:31])  # sheet name max 31 chars

        members = list(Member.objects.filter(group=group).order_by('name'))
        meetings = list(MeetingDate.objects.filter(group=group).order_by('date'))

        if not meetings:
            ws['A1'] = 'No meetings recorded yet.'
            continue

        # Build lookup: {(meeting_id, member_id): is_present}
        all_records = AttendanceRecord.objects.filter(
            meeting_date__group=group
        ).values('meeting_date_id', 'member_id', 'is_present')
        record_lookup = {(r['meeting_date_id'], r['member_id']): r['is_present'] for r in all_records}

        # Visitor counts per meeting
        visitor_counts = {}
        for v in Visitor.objects.filter(meeting_date__group=group).values('meeting_date_id'):
            mid = v['meeting_date_id']
            visitor_counts[mid] = visitor_counts.get(mid, 0) + 1

        # Header row: Date | member1 | member2 | ... | Visitors | Total
        ws.column_dimensions['A'].width = 14
        headers = ['Date'] + [m.name for m in members] + ['Visitors', 'Total Present']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center
            cell.border = border
            if col > 1:
                ws.column_dimensions[get_column_letter(col)].width = max(len(header) + 2, 10)

        # Data rows
        for row_idx, meeting in enumerate(meetings, start=2):
            # Date cell
            date_cell = ws.cell(row=row_idx, column=1, value=meeting.date.strftime('%d %b %Y'))
            date_cell.font = date_font
            date_cell.fill = date_fill
            date_cell.alignment = center
            date_cell.border = border

            # Member columns
            member_total = 0
            for col_idx, member in enumerate(members, start=2):
                is_present = record_lookup.get((meeting.pk, member.pk), False)
                value = 1 if is_present else 0
                member_total += value
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.alignment = center
                cell.border = border
                if value == 1:
                    cell.fill = PatternFill('solid', fgColor='E8F9ED')
                    cell.font = Font(color='1A7A34', bold=True)

            # Visitors column
            v_col = len(members) + 2
            v_count = visitor_counts.get(meeting.pk, 0)
            vcell = ws.cell(row=row_idx, column=v_col, value=v_count)
            vcell.alignment = center
            vcell.border = border

            # Total column
            total_cell = ws.cell(row=row_idx, column=v_col + 1, value=member_total + v_count)
            total_cell.alignment = center
            total_cell.border = border
            total_cell.font = Font(bold=True)

        # Summary row at the bottom
        sum_row = len(meetings) + 2
        ws.cell(row=sum_row, column=1, value='Total').font = Font(bold=True)
        for col_idx in range(2, len(members) + 2):
            col_letter = get_column_letter(col_idx)
            cell = ws.cell(row=sum_row, column=col_idx,
                           value=f'=SUM({col_letter}2:{col_letter}{sum_row - 1})')
            cell.font = Font(bold=True)
            cell.alignment = center
            cell.border = border

        ws.freeze_panes = 'B2'  # freeze date column and header row

    filename = f'attendance_{datetime.date.today().isoformat()}.xlsx'
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    buffer = BytesIO()
    wb.save(buffer)
    response.write(buffer.getvalue())
    return response

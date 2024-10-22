from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import EmailMessage
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from .models import EmailTrackingLog, Campaign, Template, CustomTemplate, LinkTracking
import uuid 
from .mail import customMailer
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
import json
import re
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
import base64
import mimetypes
from django.utils import timezone
import user_agents
import pytz
import json


from django.db import connection

def get_user_ip_and_location(request):
    # Get user's IP address
    user_ip = get_client_ip(request)

    if user_ip:
        # Query an external service like ipinfo.io to get geolocation info
        try:
            response = requests.get(f"http://ipinfo.io/{user_ip}/json")
            ip_data = response.json()

            # Extract location data from the response
            location_info = {
                "ip": ip_data.get("ip"),
                "city": ip_data.get("city"),
                "region": ip_data.get("region"),
                "country": ip_data.get("country"),
                "loc": ip_data.get("loc"),  # lat/long
                "org": ip_data.get("org"),  # ISP/Organization
            }

            return JsonResponse({"status": "success", "data": location_info})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Unable to get IP address"})

def get_client_ip(request):
    # Check if the client is behind a proxy (common in many web applications)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # First IP in the chain is the client's real IP
    else:
        ip = request.META.get('REMOTE_ADDR')  # Fallback to REMOTE_ADDR
    
    return ip, ip is not None

def drop_all_table():
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys=OFF;")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        for table in tables:
            if table[0] == 'sqlite_sequence':
                continue
                
            print("Table ", table[0])
            cursor.execute(f"DROP TABLE {table[0]};")
        cursor.execute("PRAGMA foreign_keys=ON;")

def initialize_template(request):
    
    return redirect('index')
    
    Template.objects.all().delete()
    template_dir = os.path.join(settings.EXAMPLES_ROOT, 'documents')
    template_path = None
        
    # Find the correct template file
    for folder in os.listdir(template_dir):
        folder_path = os.path.join(template_dir, folder)
        if os.path.isdir(folder_path) and 'inbox.html' in os.listdir(folder_path):
            template_path = os.path.join(folder_path, 'inbox.html')
            
            try:
                with open(template_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                thumbnail_path = os.path.join(folder_path, 'thumbnail.png')
                if os.path.exists(thumbnail_path):
                    thumbnail = os.path.join(settings.EXAMPLES_URL, 'documents', folder, 'thumbnail.png')
                else:
                    thumbnail = None
                    
                if html_content:
                    Template.objects.create(
                        name=folder,
                        html_content=html_content,
                        thumbnail= thumbnail,
                        created_at=datetime.now()
                    )
            except UnicodeDecodeError:
                # If UTF-8 fails, try with ISO-8859-1 encoding
                with open(template_path, 'r', encoding='iso-8859-1') as file:
                    html_content = file.read()

                thumbnail_path = os.path.join(folder_path, 'thumbnail.png')
                if os.path.exists(thumbnail_path):
                    thumbnail = os.path.join(settings.EXAMPLES_URL, 'documents', folder, 'thumbnail.png')
                else:
                    thumbnail = None

                if html_content:
                    Template.objects.create(
                        name=folder,
                        html_content=html_content,
                        thumbnail= thumbnail,
                        created_at=datetime.now()
                    )
    
    return redirect('create_campaign')

def index(request):
    campaigns = Campaign.objects.all().order_by('-created_at')
    
    # Add 5 hours and 30 minutes to created_at for each campaign
    for campaign in campaigns:
        campaign.created_at_ist = campaign.created_at + timedelta(hours=5, minutes=30)
    
    context = {
        'campaigns': campaigns
    }
    return render(request, 'index.html', context)

def campaign_page(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    
    # Add 5 hours and 30 minutes to created_at for IST
    campaign.created_at_ist = campaign.created_at + timedelta(hours=5, minutes=30)
    
    tracking_logs = EmailTrackingLog.objects.filter(campaign=campaign).order_by('recipient', '-timestamp')
    link_trackings = LinkTracking.objects.filter(campaign=campaign)

    for link_tracking in link_trackings:
        link_tracking.timestamp_ist = link_tracking.timestamp + timedelta(hours=5, minutes=30)
    
    
    recipient_data = {}
    for log in tracking_logs:
        if log.recipient not in recipient_data:
            recipient_data[log.recipient] = {
                'sent': False,
                'opened': False,
                'clicked_links': {},
                's_ipv4_address': None,
                's_ipv6_address': None,
                'c_ipv4_address': None,
                'c_ipv6_address': None,
                'device_info': None,
                'user_agent': None,
                'ip_data': log.ip_data  # Add this line
            }
        
        if log.action == 'sent':
            recipient_data[log.recipient]['sent'] = True
        elif log.action == 'email_open':
            recipient_data[log.recipient]['opened'] = True
            recipient_data[log.recipient]['s_ipv4_address'] = log.s_ipv4_address
            recipient_data[log.recipient]['s_ipv6_address'] = log.s_ipv6_address
            recipient_data[log.recipient]['c_ipv4_address'] = log.c_ipv4_address
            recipient_data[log.recipient]['c_ipv6_address'] = log.c_ipv6_address
            recipient_data[log.recipient]['ip_data'] = log.ip_data
            recipient_data[log.recipient]['device_info'] = log.device_info
            recipient_data[log.recipient]['user_agent'] = log.user_agent
        elif log.action == 'link_click':
            recipient_data[log.recipient]['clicked_links'][log.link_id] = {
                'timestamp': log.timestamp,
                's_ipv4_address': log.s_ipv4_address,
                's_ipv6_address': log.s_ipv6_address,
                'c_ipv4_address': log.c_ipv4_address,
                'ip_data': log.ip_data,
                'c_ipv6_address': log.c_ipv6_address,
                'device_info': log.device_info,
                'user_agent': log.user_agent
            }

    context = {
        'campaign': campaign,
        'recipient_data': recipient_data,
        'link_trackings': link_trackings  # Make sure this line is present
    }
    return render(request, 'show-campaign.html', context)

def create_campaign(request):
    templates = Template.objects.all()
    custom_templates = CustomTemplate.objects.all()
    
    

    context = {
        'custom_templates': custom_templates,
        'templates': templates
    }
    
    return render(request, 'add-campaign.html', context)


from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_http_methods(["POST"])
def save_custom_template(request):
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        html_content = request.POST.get('html_content')
        name = request.POST.get('name')
        is_new = request.POST.get('is_new') == 'true'
        is_scraped = request.POST.get('is_scraped') == 'true'

        try:
            if is_new or is_scraped:
                # Create a new template
                template = CustomTemplate.objects.create(
                    name=name,
                    html_content=html_content,
                )
            else:
                # Update existing template
                template = CustomTemplate.objects.get(id=template_id)
                template.name = name
                template.html_content = html_content
                template.save()

            return JsonResponse({
                'success': True,
                'message': 'Template saved successfully',
                'template_id': template.id,
                'is_new': is_new,
                'is_scraped': is_scraped
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })



@csrf_exempt
@require_http_methods(["POST"])
def update_email_tracking_log(request):
    try:
        # Print the raw request body for debugging
        print("Raw request body:", request.body)
        
        # Check if the request body is empty
        if not request.body:
            return JsonResponse({
                'success': False,
                'message': 'Empty request body',
                'error_details': 'The request body is empty'
            }, status=400)
        
        # Try to parse the JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as json_error:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data',
                'error_details': str(json_error),
                'raw_body': request.body.decode('utf-8')  # Include the raw body in the response
            }, status=400)
        
        # Print parsed data for debugging
        print("Parsed data:", data)
        
        tracking_id = data.get('tracking_id')
        link_id = data.get('link_id')
        ipv4 = data.get('ipv4')
        ipv6 = data.get('ipv6')

        if not all([tracking_id, link_id]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields',
                'error_details': 'tracking_id and link_id are required',
                'received_data': data
            }, status=400)

        log_entry = EmailTrackingLog.objects.filter(tracking_id=tracking_id, link_id=link_id).first()

        if log_entry:
            ip_data = json.loads(log_entry.ip_data)
            # Initialize combined_ip_data with existing server data
            combined_ip_data = {
                'server': ip_data.get('data', {}) if ip_data else {},
                'client': {},
                'ip': {
                    'server': {
                        'ipv4': log_entry.s_ipv4_address,
                        'ipv6': log_entry.s_ipv6_address
                    },
                    'client': {
                        'ipv4': ipv4,
                        'ipv6': ipv6
                    }
                }
            }

            # Check IPv4 and IPv6 separately
            if log_entry.s_ipv4_address != ipv4 and ipv4:
                new_ipv4_data = get_ip_data(ipv4)
                combined_ip_data['client']['ipv4'] = new_ipv4_data
            else :
                combined_ip_data['client']['ipv4'] = ip_data.get('server', {}).get('ipv4', {})

            if log_entry.s_ipv6_address != ipv6 and ipv6:
                new_ipv6_data = get_ip_data(None, ipv6)
                combined_ip_data['client']['ipv6'] = new_ipv6_data
            else :
                combined_ip_data['client']['ipv6'] = ip_data.get('server', {}).get('ipv6', {})

            # Update log entry with new data
            log_entry.c_ipv4_address = ipv4
            log_entry.c_ipv6_address = ipv6
            log_entry.ip_data = combined_ip_data
            log_entry.save()

            return JsonResponse({'success': True, 'message': 'EmailTrackingLog updated successfully'})
        else:
            return JsonResponse({
                'success': False,
                'message': 'EmailTrackingLog entry not found',
                'tracking_id': tracking_id,
                'link_id': link_id
            }, status=404)

    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': 'An error occurred',
            'error_details': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
    

def get_ip_data(ipv4, ipv6 = None):
    isIpv4 = ipv4 is not None
    isIpv6 = ipv6 is not None
    
    ipinfo_data_ipv4 = None
    ip_api_data_ipv4 = None
    shodan_data_ipv4 = None

    ipinfo_data_ipv6 = None
    ip_api_data_ipv6 = None
    shodan_data_ipv6 = None

    if ipv4 and ( ipv4 != 'localhost' or ipv4 != '127.0.0.1' or ipv4 != '::1' ) :
       
        try:
            ip_api_response = requests.get(f"http://ip-api.com/json/{ipv4}")
            ip_api_data_ipv4 = ip_api_response.json() if ip_api_response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching IP-API data for IPv4: {str(e)}")
            
        try:
            ipinfo_response = requests.get(f"https://ipinfo.io/{ipv4}/json?token=4115947f56b755")
            ipinfo_data_ipv4 = ipinfo_response.json() if ipinfo_response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching IPinfo data for IPv4: {str(e)}")

        try:
            SHODAN_API_KEY = "YOUR_SHODAN_API_KEY"
            shodan_response = requests.get(f"https://api.shodan.io/shodan/host/{ipv4}?key={SHODAN_API_KEY}")
            shodan_data_ipv4 = shodan_response.json() if shodan_response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching Shodan data for IPv4: {str(e)}")

    if ipv6 and ( ipv6 != 'localhost' or ipv6 != '::1' or ipv6 != '0:0:0:0:0:0:0:1' ) :
        try:
            ipinfo_response = requests.get(f"https://ipinfo.io/{ipv6}/json?token=4115947f56b755")
            ipinfo_data_ipv6 = ipinfo_response.json() if ipinfo_response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching IPinfo data for IPv6: {str(e)}")

    if isIpv4 and isIpv6:
        return {
            'ipv4' : {
                'Shodan': shodan_data_ipv4,
                'IP-info' : ipinfo_data_ipv4,
                'IP-API' : ip_api_data_ipv4
            },
            'ipv6' : {
                'Shodan': shodan_data_ipv6,
                'IP-info' : ipinfo_data_ipv6,
                'IP-API' : ip_api_data_ipv6
            },          
        }
    elif isIpv4 and not isIpv6:
        return {
            'IP-info': ipinfo_data_ipv4,
            'IP-API': ip_api_data_ipv4,
            'Shodan': shodan_data_ipv4
        }
    elif not isIpv4 and isIpv6:
        return {
            'IP-info': ipinfo_data_ipv6,
            'IP-API': ip_api_data_ipv6,
            'Shodan': shodan_data_ipv6
        }


def track_link(request, tracking_id, link_id):
    link_tracking = get_object_or_404(LinkTracking, tracking_id=tracking_id, link_id=link_id)
    
    # Parse user agent
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = user_agents.parse(user_agent_string)

    # Collect device and browser information
    device_info = {
        'browser': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string,
        'os': user_agent.os.family,
        'os_version': user_agent.os.version_string,
        'device': user_agent.device.family,
        'is_mobile': user_agent.is_mobile,
        'is_tablet': user_agent.is_tablet,
        'is_pc': user_agent.is_pc,
    }

    # Get both IPv4 and IPv6 addresses
    client_ip, is_routable = get_client_ip(request)
    ipv4 = client_ip if ':' not in client_ip else None
    ipv6 = client_ip if ':' in client_ip else None
    f = 0

    if ipv4 and ipv6:
        ip_data = get_ip_data(ipv4, ipv6)
    elif ipv4:
        f=1
        ip_data = get_ip_data(ipv4)
    elif ipv6:
        f=2
        ip_data = get_ip_data(None, ipv6)
    
    if f == 1:
        ip_data = {'ipv4': ip_data}
    elif f == 2:
        ip_data = {'ipv6': ip_data}

    ip_data = {
        'data': ip_data,
        'server': ip_data,
        'ip' : {
            'ipv4': ipv4,
            'ipv6': ipv6
        }
    }
    
    ip_data_str = json.dumps(ip_data)
    # Log link click
    EmailTrackingLog.objects.create(
        campaign=link_tracking.campaign,
        tracking_id=tracking_id,
        link_id=link_id,
        recipient=link_tracking.campaign.tracking_logs.filter(tracking_id=tracking_id).first().recipient,
        action='link_click',
        s_ipv4_address=ipv4,
        s_ipv6_address=ipv6,
        ip_data=ip_data_str,
        user_agent=user_agent_string,
        device_info=device_info
    )
    
    # Update link tracking
    link_tracking.clicks += 1
    link_tracking.last_clicked = timezone.now()
    link_tracking.save()
    
    # Redirect to the landing page with the original link as a parameter
    landing_page_url = reverse('landing_page')
    redirect_url = f"{landing_page_url}?redirect={link_tracking.original_link}&tracking_id={tracking_id}&link_id={link_id}"
    return redirect(redirect_url)

def landing_page(request):
    return render(request, 'landing-page.html')

@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            template_id = data.get('template_id')
            personalized_content = ""
            template = None
            try:
                template = Template.objects.get(id=template_id)
            except Template.DoesNotExist:
                try:
                    template = CustomTemplate.objects.get(id=template_id)
                except CustomTemplate.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Invalid template id'})
           
            html_content = template.html_content

            campaign = Campaign.objects.create(
                name=(data['campaign_name'] or 'Untitled'),
                template_id=template_id,
                scheduled_time=timezone.make_aware(datetime.fromisoformat(data['scheduled_time']), pytz.UTC) if data['scheduled_time'] else None,
                is_recurring=data['is_recurring'],
                recurrence_pattern=data['recurrence_pattern'] if data['is_recurring'] else None,
                recurrence_interval=data.get('recurrence_interval', 1),
                recurrence_count=data.get('recurrence_count', 0)
            )

            # Handle direct attachment
            attachment_data = data.get('attachment')
            if attachment_data:
                mime_type, base64_data = attachment_data.split(';base64,')
                file_extension = mimetypes.guess_extension(mime_type.split(':')[1])
                file_name = f"attachment_{uuid.uuid4().hex}{file_extension}"
                file_content = base64.b64decode(base64_data)
                campaign.attachment.save(file_name, ContentFile(file_content))

            # Handle attachment link
            attachment_link = data.get('attachment_link')
            if attachment_link:
                campaign.original_attachment_link = attachment_link
                campaign.save()

            # Parse sender information
            sender_match = re.match(r'(.*)<(.+@(.+))>', data['from'])
            if sender_match:
                from_name, from_email, from_domain = sender_match.groups()
            else:
                from_name, from_email, from_domain = '', data['from'], data['from'].split('@')[-1]

            # Replace sender placeholders in the template
            html_content = html_content.replace('{{From Name}}', from_name.strip())
            html_content = html_content.replace('{{From Email}}', from_email.strip())
            html_content = html_content.replace('{{From Domain}}', from_domain.strip())

            # Create a list of all recipients (to, cc, bcc)
            all_recipients = data['to'] + (data['cc'] or []) + (data['bcc'] or [])

            if campaign.scheduled_time and campaign.scheduled_time > timezone.now():
                return JsonResponse({'success': True, 'message': 'Campaign scheduled successfully!', 'campaign_id': campaign.id, 'redirect_url': reverse('campaign_page', args=[campaign.id])})
            else:
                # Existing email sending logic
                for recipient in all_recipients:
                    if recipient == "" or recipient == None or recipient.strip() == "":
                        continue
                    
                    # Parse recipient information
                    recipient_match = re.match(r'(.*)<(.+@(.+))>', recipient)
                    if recipient_match:
                        to_name, to_email, to_domain = recipient_match.groups()
                    else:
                        to_name, to_email, to_domain = '', recipient, recipient.split('@')[-1]

                    tracking_id = str(uuid.uuid4())

                    # Replace all links with tracking links
                    def replace_link(match):
                        original_link = match.group(1)
                        link_id = str(uuid.uuid4())[:8]  # Generate a short unique ID for each link
                        tracking_link = request.build_absolute_uri(reverse('track_link', args=[tracking_id, link_id]))
                        
                        # Store the link information in the database
                        LinkTracking.objects.create(
                            campaign=campaign,
                            original_link=original_link,
                            tracking_link=tracking_link,
                            link_id=link_id,
                            tracking_id=tracking_id
                        )
                        
                        return f'href="{tracking_link}"'

                    personalized_content = re.sub(r'href="([^"]*)"', replace_link, html_content)

                    # Replace recipient placeholders
                    personalized_content = personalized_content.replace('{{To Name}}', to_name.strip())
                    personalized_content = personalized_content.replace('{{To Email}}', to_email.strip())
                    personalized_content = personalized_content.replace('{{To Domain}}', to_domain.strip())

                    # Add tracking pixel
                    pixel_link = request.build_absolute_uri(reverse('track_pixel', args=[tracking_id]))
                    personalized_content += f'<img src="{pixel_link}" width="1" height="1" />'

                    try:
                        # When sending emails in your views, use the updated send_email function
                        success, message = customMailer(to_email, data['subject'], personalized_content)
                        if not success:
                            # Handle the error (e.g., log it, show a message to the user)
                            print(f"Failed to send email: {message}")
                        
                        # Log the sent email
                        EmailTrackingLog.objects.create(
                            campaign=campaign,
                            recipient=to_email,
                            tracking_id=tracking_id,
                            action='sent'
                        )
                    except Exception as e:
                        return JsonResponse({'success': False, 'error': str(e)})

                return JsonResponse({
                    'success': True, 
                    'message': 'Emails sent successfully!', 
                    'campaign_id': campaign.id,
                    'redirect_url': reverse('campaign_page', args=[campaign.id])
                })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON in request body'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def track_pixel(request, tracking_id):
    # Find the EmailTrackingLog entry for this tracking_id
    tracking_log = get_object_or_404(EmailTrackingLog, tracking_id=tracking_id)
    
    # Get both IPv4 and IPv6 addresses
    client_ip, is_routable = get_client_ip(request)
    ipv4 = client_ip if ':' not in client_ip else None
    ipv6 = client_ip if ':' in client_ip else None

    # Log email open
    EmailTrackingLog.objects.create(
        campaign=tracking_log.campaign,
        tracking_id=tracking_id,
        recipient=tracking_log.recipient,
        action='email_open',
        ipv4_address=ipv4,
        ipv6_address=ipv6
    )
    # Return a transparent 1x1 pixel
    return HttpResponse(content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b', content_type='image/gif')

def edit_template(request, template_id):
    # Try to get a custom template first
    template = None
    try:
        template = CustomTemplate.objects.get(id=template_id)
        is_custom = True
    except CustomTemplate.DoesNotExist:
        template = Template.objects.get(id=template_id)
        is_custom = False

    if request.method == 'POST':
        # Get the updated content from the request
        updated_content = request.POST.get('content')
        
        if is_custom:
            # If it's already a custom template, just update it
            template.content = updated_content
            template.save()
        else:
            # If it's a regular template, create a new custom template
            new_custom_template = CustomTemplate.objects.create(
                name=f"Custom {template.name}",
                content=updated_content,
                original_template=template
            )
            template = new_custom_template

        return JsonResponse({'success': True, 'template_id': template.id})

    # If it's a GET request, just render the edit template
    return render(request, 'edit_template.html', {'template': template})

def new_template(request):
    template = None
    return render(request, 'edit_template.html',  {'template': template})

# You might need to add this function if it doesn't exist
def edit_default_template(request, template_id):
    template = get_object_or_404(Template, id=template_id)
    context = {
        'template': template,
        'is_default': True
    }
    return render(request, 'edit_template.html', context)

from django.http import FileResponse
from django.shortcuts import get_object_or_404

def download_attachment(request, campaign_id, tracking_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)
    tracking_log = get_object_or_404(EmailTrackingLog, tracking_id=tracking_id)
    
    # Log the attachment download attempt
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    EmailTrackingLog.objects.create(
        campaign=campaign,
        tracking_id=tracking_id,
        recipient=tracking_log.recipient,
        action='attachment_download',
        ip_address=client_ip
    )
    
    if campaign.attachment:
        # Serve the file
        return FileResponse(campaign.attachment.open(), as_attachment=True, filename=campaign.attachment.name)
    elif campaign.original_attachment_link:
        # Redirect to the original attachment link
        return redirect(campaign.original_attachment_link)
    else:
        return HttpResponse("No attachment found", status=404)
    
    
from bs4 import BeautifulSoup
import requests
import random 
from collections import OrderedDict
from urllib.parse import urljoin
from fake_useragent import UserAgent

from urllib.request import urlopen

def test(request):
    url = 'https://getbootstrap.com/docs/5.3/customize/color-modes/'
    
    headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
    r = requests.Session()
        
    r.headers = headers

    response = r.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    for script_tag in soup.find_all('script'):
        script_tag.decompose()
        
    body = soup.find('body')
    
    css_links = []
    for link_tag in soup.find_all('link', rel='stylesheet'):
        css_link = link_tag.get('href')
        if css_link:
            absolute_css_link = urljoin(url, css_link)
            css_links.append(absolute_css_link)
    
    # Fetch CSS content from all external links
    css_content = ''
    for css_link in css_links:
        css_response = requests.get(css_link)
        css_content += f"<style>{css_response.text}</style>\n"


    # Combine the body content and the CSS inside a <style> tag
    combined_content = f"{css_content}\n{body.prettify()}"

    template = {
        'html_content': combined_content,
    }
    return render(request, 'test.html', {'template': template})


    
def scrape_url(request, url=None):
    if url is None:
        url = request.GET.get('scrape')
        
    headers_list = [
        # Firefox 77 Mac
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
        # Firefox 77 Windows
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
        # Chrome 83 Mac
        {
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://www.google.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        # Chrome 83 Windows 
        {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "https://www.google.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9"
        }
    ]
    # Create ordered dict from Headers above
    ordered_headers_list = []
    for headers in headers_list:
        h = OrderedDict()
        for header,value in headers.items():
            h[header]=value
        ordered_headers_list.append(h)
    
    if not url:
        return JsonResponse({'error': 'URL is required'}, status=400)
    try:
        
        
        headers = random.choice(headers_list)
        #Create a request session
        
        r = requests.Session()
        
        r.headers = headers

        response = r.get(url)
                
        soup = BeautifulSoup(response.content, 'html.parser')
        
        
            
        for script_tag in soup.find_all('script'):
            script_tag.decompose()
            
        body = soup.find('body')
        
        css_links = []
        for link_tag in soup.find_all('link', rel='stylesheet'):
            css_link = link_tag.get('href')
            if css_link:
                absolute_css_link = urljoin(url, css_link)
                css_links.append(absolute_css_link)
        
        # Fetch CSS content from all external links
        css_content = ''
        for css_link in css_links:
            css_response = requests.get(css_link)
            css_content += f"<style>{css_response.text}</style>\n"


        inline_styles = ''
        for style_tag in soup.find_all('style'):
            inline_styles += f"<style>{style_tag.string}</style>\n"
        
        # Combine the inline styles, external styles, and body content
        combined_content = f"{inline_styles}\n{css_content}\n{body.prettify()}"



        # # Extract CSS links
        # css_links = []
        # for link_tag in soup.find_all('link', rel='stylesheet'):
        #     css_link = link_tag.get('href')
        #     if css_link:
        #         # Convert to absolute URL
        #         absolute_css_link = urljoin(url, css_link)
        #         css_links.append(absolute_css_link)
        #         link_tag.decompose()

        # # Extract JS links
        # js_links = []
        # for script_tag in soup.find_all('script', src=True):
        #     js_link = script_tag.get('src')
        #     if js_link:
        #         # Convert to absolute URL
        #         absolute_js_link = urljoin(url, js_link)
        #         js_links.append(absolute_js_link)
        #         script_tag.decompose()

        # js_content = ''
        # # for js_link in js_links:
        # #     js_response = r.get(js_link)
        # #     js_content += f"<script>{js_response.text}</script>\n"

        # # Prepare the CSS content
        # css_content = ''
        # for css_link in css_links:
        #     css_response = r.get(css_link)
        #     css_content += f"<style>{css_response.text}</style>\n"

        # # Prettify the HTML
        # html_content = soup.prettify()

        # # Insert CSS into HTML before rendering
        # head_end_index = html_content.index('</head>')
        # full_html_content = (
        #     f"{html_content[:head_end_index]}"
        #     f"{css_content}\n"
        #     f"{js_content}\n"
        #     f"{html_content[head_end_index:]}"
        # )
        # print(full_html_content)
        return render(request, 'edit_template.html', {
            'template': {
                'html_content': combined_content
            },
            'is_new': True,
            'is_scraped': True
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 500,
            'url': url
        }, status=500)

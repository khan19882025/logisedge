from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from hr_letters_documents.models import (
    LetterType, LetterTemplate, DocumentCategory
)
from employees.models import Employee, Department
import random

class Command(BaseCommand):
    help = 'Create sample data for HR Letters & Documents module'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for HR Letters & Documents...')
        
        # Create sample letter types
        letter_types_data = [
            {
                'name': 'Offer Letter',
                'description': 'Official offer of employment to a candidate'
            },
            {
                'name': 'Appointment Letter',
                'description': 'Confirmation of appointment after probation period'
            },
            {
                'name': 'Salary Certificate',
                'description': 'Certificate confirming employee salary details'
            },
            {
                'name': 'Employment Verification Letter',
                'description': 'Letter for external verification of employment'
            },
            {
                'name': 'NOC (No Objection Certificate)',
                'description': 'No objection certificate for various purposes'
            },
            {
                'name': 'Warning Letter',
                'description': 'Formal warning for policy violations or performance issues'
            },
            {
                'name': 'Experience/Relieving Letter',
                'description': 'Letter confirming employment experience and relieving'
            },
            {
                'name': 'Termination Letter',
                'description': 'Official termination of employment'
            },
            {
                'name': 'Resignation Acceptance',
                'description': 'Acceptance of employee resignation'
            },
            {
                'name': 'Visa Request Letter',
                'description': 'Letter requesting visa for business travel'
            }
        ]
        
        created_letter_types = []
        for data in letter_types_data:
            letter_type, created = LetterType.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'is_active': True
                }
            )
            created_letter_types.append(letter_type)
            if created:
                self.stdout.write(f'Created letter type: {letter_type.name}')
        
        # Create sample letter templates
        templates_data = [
            {
                'letter_type_name': 'Offer Letter',
                'title': 'Standard Offer Letter',
                'subject': 'Offer of Employment - {{employee_name}}',
                'content': '''Dear {{employee_name}},

We are pleased to offer you the position of {{designation}} in our {{department}} department.

Position Details:
- Designation: {{designation}}
- Department: {{department}}
- Employee ID: {{employee_id}}
- Date of Joining: {{date_of_joining}}
- Salary: {{salary}} per month

Please review the attached terms and conditions. If you accept this offer, please sign and return this letter within 7 days.

We look forward to welcoming you to our team.

Best regards,
HR Department
{{company_name}}''',
                'arabic_content': '''عزيزي {{employee_name}}،

يسرنا أن نقدم لك منصب {{designation}} في قسم {{department}}.

تفاصيل المنصب:
- المسمى الوظيفي: {{designation}}
- القسم: {{department}}
- رقم الموظف: {{employee_id}}
- تاريخ الانضمام: {{date_of_joining}}
- الراتب: {{salary}} شهرياً

يرجى مراجعة الشروط والأحكام المرفقة. إذا قبلت هذا العرض، يرجى التوقيع وإرجاع هذه الرسالة خلال 7 أيام.

نتطلع إلى الترحيب بك في فريقنا.

مع أطيب التحيات،
قسم الموارد البشرية
{{company_name}}'''
            },
            {
                'letter_type_name': 'Warning Letter',
                'title': 'Performance Warning Letter',
                'subject': 'Warning Letter - Performance Issues',
                'content': '''Dear {{employee_name}},

This letter serves as a formal warning regarding your performance issues.

Employee Details:
- Name: {{employee_name}}
- Employee ID: {{employee_id}}
- Department: {{department}}
- Designation: {{designation}}

Issue Date: {{issue_date}}

We have observed that your performance has not met the expected standards. Please take immediate steps to improve your performance.

This warning will remain in your file for 6 months. Further performance issues may result in disciplinary action.

Please acknowledge receipt of this letter by signing below.

Best regards,
HR Department
{{company_name}}''',
                'arabic_content': '''عزيزي {{employee_name}}،

هذه الرسالة بمثابة تحذير رسمي بخصوص مشاكل الأداء.

تفاصيل الموظف:
- الاسم: {{employee_name}}
- رقم الموظف: {{employee_id}}
- القسم: {{department}}
- المسمى الوظيفي: {{designation}}

تاريخ المشكلة: {{issue_date}}

لاحظنا أن أداءك لم يصل إلى المعايير المتوقعة. يرجى اتخاذ خطوات فورية لتحسين أدائك.

سيبقى هذا التحذير في ملفك لمدة 6 أشهر. قد تؤدي مشاكل الأداء الإضافية إلى إجراءات تأديبية.

يرجى الإقرار باستلام هذه الرسالة بالتوقيع أدناه.

مع أطيب التحيات،
قسم الموارد البشرية
{{company_name}}'''
            },
            {
                'letter_type_name': 'Salary Certificate',
                'title': 'Standard Salary Certificate',
                'subject': 'Salary Certificate - {{employee_name}}',
                'content': '''To Whom It May Concern,

This is to certify that {{employee_name}} (Employee ID: {{employee_id}}) is currently employed with {{company_name}}.

Employment Details:
- Name: {{employee_name}}
- Employee ID: {{employee_id}}
- Designation: {{designation}}
- Department: {{department}}
- Date of Joining: {{date_of_joining}}
- Current Salary: {{salary}} per month

This certificate is issued on {{issue_date}} for official purposes.

Best regards,
HR Department
{{company_name}}''',
                'arabic_content': '''لمن يهمه الأمر،

هذا لتأكيد أن {{employee_name}} (رقم الموظف: {{employee_id}}) يعمل حالياً في {{company_name}}.

تفاصيل التوظيف:
- الاسم: {{employee_name}}
- رقم الموظف: {{employee_id}}
- المسمى الوظيفي: {{designation}}
- القسم: {{department}}
- تاريخ الانضمام: {{date_of_joining}}
- الراتب الحالي: {{salary}} شهرياً

تم إصدار هذه الشهادة في {{issue_date}} للأغراض الرسمية.

مع أطيب التحيات،
قسم الموارد البشرية
{{company_name}}'''
            }
        ]
        
        for template_data in templates_data:
            letter_type = next((lt for lt in created_letter_types if lt.name == template_data['letter_type_name']), None)
            if letter_type:
                template, created = LetterTemplate.objects.get_or_create(
                    title=template_data['title'],
                    letter_type=letter_type,
                    defaults={
                        'subject': template_data['subject'],
                        'content': template_data['content'],
                        'arabic_content': template_data['arabic_content'],
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created template: {template.title}')
        
        # Create sample document categories
        categories_data = [
            {
                'name': 'Employment Documents',
                'description': 'Documents related to employment contracts and agreements'
            },
            {
                'name': 'Performance Documents',
                'description': 'Performance reviews, warnings, and improvement plans'
            },
            {
                'name': 'Legal Documents',
                'description': 'Legal notices, compliance documents, and policy updates'
            },
            {
                'name': 'Certificates',
                'description': 'Employment certificates, experience letters, and verifications'
            }
        ]
        
        for category_data in categories_data:
            category, created = DocumentCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created document category: {category.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data for HR Letters & Documents module!')
        )
        self.stdout.write(f'Created {len(created_letter_types)} letter types')
        self.stdout.write(f'Created {len(templates_data)} letter templates')
        self.stdout.write(f'Created {len(categories_data)} document categories') 
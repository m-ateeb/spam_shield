"""
Management command to recalculate confidence scores for existing classification results
"""
from django.core.management.base import BaseCommand
from email_connector.models import ClassificationResult, Email, EmailAuthResult, URLAnalysis


class Command(BaseCommand):
    help = 'Recalculate confidence scores for existing classification results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Recalculate scores for all classification results (not just those with 0.0)',
        )

    def calculate_confidence_score(self, email_obj, auth_result, url_analyses, verdict, auth_score):
        """Calculate confidence score based on analysis results."""
        url_results = [u.final_verdict for u in url_analyses]
        url_pending = url_results.count("pending")
        url_safe = url_results.count("safe")
        url_suspicious = url_results.count("suspicious")
        url_malicious = url_results.count("malicious")
        
        spf = auth_result.spf_status
        dkim = auth_result.dkim_status
        dmarc = auth_result.dmarc_status
        
        auth_failures = sum(1 for s in [spf, dkim, dmarc] if s in ["fail", "reject", "quarantine"])
        auth_passes = sum(1 for s in [spf, dkim, dmarc] if s == "pass")
        
        confidence_score = 0.0
        
        # Calculate confidence based on verdict
        if url_malicious > 0 or verdict == "phishing":
            # High confidence (85-95%) when malicious URLs are detected or phishing verdict
            if url_malicious > 0:
                confidence_score = min(95.0, 85.0 + (url_malicious * 3.0))
            else:
                # High confidence for very low auth scores: 80-95%
                confidence_score = min(95.0, 80.0 + ((20 - auth_score) * 0.75))
                if url_suspicious > 0:
                    confidence_score = min(95.0, confidence_score + (url_suspicious * 2.0))
        elif verdict == "suspicious":
            # Medium-high confidence for suspicious: 65-85%
            confidence_score = 65.0 + ((40 - auth_score) * 1.0)
            if url_suspicious > 0:
                confidence_score = min(90.0, confidence_score + (url_suspicious * 3.0))
        elif verdict == "safe":
            # High confidence for safe emails: 75-95%
            confidence_score = 75.0 + ((auth_score - 40) * 0.33)
            if url_suspicious > 0:
                confidence_score = max(70.0, confidence_score - (url_suspicious * 2.0))
        
        # Adjust confidence based on authentication results
        if verdict in ["phishing", "suspicious"]:
            if auth_failures >= 2:
                confidence_score = min(95.0, confidence_score + 5.0)
            elif auth_failures == 1:
                confidence_score = min(95.0, confidence_score + 2.0)
        elif verdict == "safe":
            if auth_passes >= 2:
                confidence_score = min(95.0, confidence_score + 5.0)
            elif auth_passes == 1:
                confidence_score = min(95.0, confidence_score + 2.0)
        
        # Ensure confidence is within valid range (50-100)
        confidence_score = max(50.0, min(100.0, confidence_score))
        
        return round(confidence_score, 1)

    def handle(self, *args, **options):
        recalculate_all = options['all']
        
        # Get classification results to update
        if recalculate_all:
            classifications = ClassificationResult.objects.all()
            self.stdout.write('Recalculating confidence scores for ALL classification results...')
        else:
            classifications = ClassificationResult.objects.filter(confidence_score=0.0)
            self.stdout.write('Recalculating confidence scores for classification results with score 0.0...')
        
        updated_count = 0
        skipped_count = 0
        
        for classification in classifications:
            try:
                email_obj = classification.email
                
                # Get auth results
                try:
                    auth_result = email_obj.auth_result
                except EmailAuthResult.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping email {email_obj.id}: No auth result')
                    )
                    skipped_count += 1
                    continue
                
                # Get URL analyses
                url_analyses = URLAnalysis.objects.filter(email=email_obj)
                
                # Calculate new confidence score
                new_score = self.calculate_confidence_score(
                    email_obj,
                    auth_result,
                    url_analyses,
                    classification.rule_engine_verdict,
                    email_obj.auth_score
                )
                
                # Update if score changed
                if classification.confidence_score != new_score:
                    classification.confidence_score = new_score
                    classification.save(update_fields=['confidence_score'])
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing classification {classification.id}: {str(e)}')
                )
                skipped_count += 1
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} confidence scores. '
                f'Skipped {skipped_count} records.'
            )
        )


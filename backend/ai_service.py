from openai import OpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)

async def generate_redirect_recommendation(error_url: str, site_url: str, existing_pages: list = None):
    """
    Generate AI recommendation for where to redirect a 404 URL
    """
    existing_pages_str = "\n".join(existing_pages[:20]) if existing_pages else "No existing pages provided"
    
    prompt = f"""You are an SEO expert helping with 404 error recovery.

A 404 error was found for this URL:
{error_url}

On site: {site_url}

Existing pages on the site:
{existing_pages_str}

Task: Recommend the best existing page to redirect this 404 URL to, or suggest creating new content.

Provide your response in this format:
REDIRECT_TARGET: [URL of the best page to redirect to, or 'CREATE_NEW' if new content should be created]
REASON: [Brief explanation of why this is the best choice]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an SEO expert specializing in 404 error recovery and redirect strategies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        
        # Parse response
        lines = content.strip().split("\n")
        redirect_target = None
        reason = None
        
        for line in lines:
            if line.startswith("REDIRECT_TARGET:"):
                redirect_target = line.replace("REDIRECT_TARGET:", "").strip()
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
        
        return {
            "redirect_target": redirect_target,
            "reason": reason
        }
    
    except Exception as e:
        logger.error(f"Failed to generate redirect recommendation: {e}")
        return {
            "redirect_target": None,
            "reason": f"AI recommendation failed: {str(e)}"
        }

async def generate_content_suggestion(error_url: str, site_url: str, backlink_count: int = 0):
    """
    Generate AI suggestion for what content should be created to replace the 404
    """
    prompt = f"""You are an SEO content strategist.

A 404 error was found for: {error_url}
On site: {site_url}
This URL has {backlink_count} backlinks pointing to it.

Task: Suggest what type of content should be created for this URL to:
1. Satisfy the intent of the original URL
2. Provide value to visitors arriving via backlinks
3. Improve SEO

Provide a brief, actionable content suggestion (2-3 sentences).
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an SEO content strategist helping create content to replace 404 pages."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        suggestion = response.choices[0].message.content.strip()
        return suggestion
    
    except Exception as e:
        logger.error(f"Failed to generate content suggestion: {e}")
        return f"AI content suggestion failed: {str(e)}"
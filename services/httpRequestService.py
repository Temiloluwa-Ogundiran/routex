import httpx
import logging

logger = logging.getLogger(__name__)

async def get_request(url, headers= None, data= None):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=15)
            return response.json(), response.status_code
    except Exception as e:
        logger.error(f'An error occured while sending request to: {url}. Error: {e}')
        return {'status': 'failed'}, 500

async def post_request(url, headers= None, data= None, proxy_url = None):
    try:
        async with httpx.AsyncClient(proxy= proxy_url) as client:
            response = await client.post(url, headers=headers, data= data, timeout=15)
            return response.json(), response.status_code
    except Exception as e:
        logger.error(f'An error occured while sending request to: {url}. Error: {e}')
        return {'status': 'failed'}, 500
    
